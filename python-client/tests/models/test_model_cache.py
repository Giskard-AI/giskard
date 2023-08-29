import copy
import math

import numpy as np
import pandas as pd
import xxhash
from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM

import giskard
from giskard import Dataset, Model
from giskard.core.core import SupportedModelTypes
from giskard.models.cache import ModelCache


def test_model_prediction_is_cached_on_text_generation_model():
    llm = FakeListLLM(responses=['This is my text with special chars" → ,.!? # and \n\nnewlines', "This is my text"])

    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(
        pd.DataFrame({"instruct": ["Test 1", "Test 2"]}),
        column_types={
            "instruct": "text",
        },
    )
    model.predict(dataset)

    # Should load from cache
    assert model.predict(dataset).raw_prediction.tolist() == llm.responses
    assert model.predict(dataset).raw_prediction.tolist() == llm.responses

    # Test cache persistence
    model_id = model.id

    del model
    model = Model(chain, model_type="text_generation", id=model_id.hex)

    assert model.predict(dataset).raw_prediction.tolist() == llm.responses


def test_model_prediction_is_cached_on_regression_model():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(prediction_function, model_type="regression")

    wrapped_dataset = Dataset(df=pd.DataFrame([12.0, 1, 23, 4, 5, 6, 7, 8, 9, 10.0]))

    prediction = wrapped_model.predict(wrapped_dataset)
    cached_prediction = wrapped_model.predict(wrapped_dataset)

    assert called_indexes == list(wrapped_dataset.df.index), "The  prediction should have been called once"
    assert list(prediction.raw) == [12.0, 1, 23, 4, 5, 6, 7, 8, 9, 10.0]
    assert list(prediction.raw) == list(cached_prediction.raw)
    assert list(prediction.raw_prediction) == list(cached_prediction.raw_prediction)
    assert list(prediction.prediction) == list(cached_prediction.prediction)
    assert prediction.probabilities == cached_prediction.probabilities


def test_model_prediction_is_cached_on_classification_model(german_credit_catboost, german_credit_data):
    model = german_credit_catboost
    dataset = german_credit_data

    _predict_df = copy.copy(model.predict_df)

    def predict_df(*args, **kwargs):
        predict_df.num_calls += 1
        return _predict_df(*args, **kwargs)

    predict_df.num_calls = 0
    model.predict_df = predict_df

    prediction = model.predict(dataset)
    model.predict(dataset)
    model.predict(dataset)
    cached_prediction = model.predict(dataset)

    assert predict_df.num_calls == 1, "The prediction should have been called once"
    assert (prediction.raw == cached_prediction.raw).all()
    assert (prediction.raw_prediction == cached_prediction.raw_prediction).all()
    assert list(prediction.prediction) == list(cached_prediction.prediction)

    # Test with no cache
    with giskard.models.cache.no_cache():
        model.predict(dataset)
        assert model.predict_df.num_calls == 2
        model.predict(dataset)
        assert model.predict_df.num_calls == 3


def test_predict_disabled_cache():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(prediction_function, model_type="regression")

    wrapped_dataset = Dataset(df=pd.DataFrame([0, 1]))
    with giskard.models.cache.no_cache():
        prediction = wrapped_model.predict(wrapped_dataset)
        second_prediction = wrapped_model.predict(wrapped_dataset)

    assert called_indexes == list(wrapped_dataset.df.index) + list(
        wrapped_dataset.df.index
    ), "The prediction should have been called twice"
    assert list(prediction.raw) == list(second_prediction.raw)
    assert list(prediction.raw_prediction) == list(second_prediction.raw_prediction)
    assert list(prediction.prediction) == list(second_prediction.prediction)
    assert prediction.probabilities == second_prediction.probabilities


def test_predict_only_recompute_transformed_values():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(prediction_function, model_type="regression")

    wrapped_dataset = Dataset(df=pd.DataFrame([0, 1]))

    prediction = wrapped_model.predict(wrapped_dataset)

    def replace_row_one(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, 0] = 2
        return df

    transformed_dataset = wrapped_dataset.transform(replace_row_one, row_level=False)
    second_prediction = wrapped_model.predict(transformed_dataset)

    assert called_indexes == list(wrapped_dataset.df.index) + [
        1
    ], "The  prediction should have been called once for row 0 and twice of row 1"
    assert list(prediction.raw) != list(second_prediction.raw)
    assert list(prediction.raw_prediction) != list(second_prediction.raw_prediction)
    assert list(prediction.prediction) != list(second_prediction.prediction)


def test_predict_with_complex_dataset():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df["foo"].values)

    wrapped_model = Model(prediction_function, model_type="regression")

    wrapped_dataset = Dataset(
        df=pd.DataFrame(
            [{"foo": 42, "bar": "Hello world!", "baz": True}, {"foo": 3.14, "bar": "This is a test", "baz": False}]
        )
    )

    prediction = wrapped_model.predict(wrapped_dataset)

    def replace_row_one(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, "foo"] = 42
        return df

    transformed_dataset = wrapped_dataset.transform(replace_row_one, row_level=False)
    second_prediction = wrapped_model.predict(transformed_dataset)

    assert called_indexes == list(wrapped_dataset.df.index) + [
        1
    ], "The  prediction should have been called once for row 0 and twice of row 1"
    assert list(prediction.raw) != list(second_prediction.raw)
    assert list(prediction.raw_prediction) != list(second_prediction.raw_prediction)
    assert list(prediction.prediction) != list(second_prediction.prediction)


def test_model_cache_multiple_index_type():
    model_cache = ModelCache(SupportedModelTypes.REGRESSION)
    hashes = list(map(lambda x: xxhash.xxh3_128_hexdigest(str(x)), [-18313, 42, 184391849]))

    int_idx = pd.Series(hashes, index=[-18313, 42, 184391849])
    int_cache = model_cache.read_from_cache(int_idx)
    assert list(int_idx.index) == list(int_cache.index)
    assert int_cache.isna().all()

    str_idx = pd.Series(hashes, index=["Test", "42", "Hello world!"])
    str_cache = model_cache.read_from_cache(str_idx)
    assert list(str_idx.index) == list(str_cache.index)
    assert str_cache.isna().all()

    cache_df = model_cache._to_df()
    assert len(cache_df) == 0

    result = np.array([[1, 2], [3, 4]])
    model_cache.set_cache(pd.Series(hashes[1:]), result)

    cache_df = model_cache._to_df()
    assert len(cache_df) == 2
    assert hashes[1:] == list(cache_df.index)
    assert [1, 3] == list(cache_df[0].values)
    assert [2, 4] == list(cache_df[1].values)

    int_cache = model_cache.read_from_cache(int_idx)
    assert list(int_idx.index) == list(int_cache.index)
    assert (result == int_cache[1:].values.tolist()).all()
    assert math.isnan(int_cache.iloc[0])

    str_cache = model_cache.read_from_cache(str_idx)
    assert list(str_idx.index) == list(str_cache.index)
    assert (result == str_cache[1:].values.tolist()).all()
    assert math.isnan(str_cache.iloc[0])
