import pandas as pd
import pytest

import giskard
import giskard.testing.tests.metamorphic as metamorphic
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.transformation_function import transformation_function


def _test_metamorphic_increasing_regression(ds: Dataset, model, threshold):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.bmi = x.bmi + x.bmi * 0.1
        return x

    results = metamorphic.test_metamorphic_increasing(
        model=model, dataset=ds, transformation_function=perturbation, threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.44
    return results.passed


def _test_metamorphic_decreasing_regression(ds: Dataset, model, threshold):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.age = x.age - x.age * 0.1
        return x

    results = metamorphic.test_metamorphic_decreasing(
        model=model, dataset=ds, transformation_function=perturbation, threshold=threshold
    ).execute()
    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.54
    return results.passed


def _test_metamorphic_increasing_classification(df, model, threshold):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.duration_in_month = x.duration_in_month + x.duration_in_month * 0.5
        return x

    results = metamorphic.test_metamorphic_increasing(
        model=model,
        dataset=df,
        transformation_function=perturbation,
        threshold=threshold,
        classification_label=model.meta.classification_labels[0],
    ).execute()

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def _test_metamorphic_decreasing_classification(df, model, threshold):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.duration_in_month = x.duration_in_month * 0.5
        return x

    results = metamorphic.test_metamorphic_decreasing(
        model=model,
        dataset=df,
        transformation_function=perturbation,
        threshold=threshold,
        classification_label=model.meta.classification_labels[0],
    ).execute()

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model, 0.8)


def test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model, 0.8)


def test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.3)
    assert not _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)


def test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)
    assert not _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.6)


def test_metamorphic_decreasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):

        @transformation_function()
        def perturbation(x: pd.Series) -> pd.Series:
            x.duration_in_month = x.duration_in_month * 0.5
            return x

        metamorphic.test_metamorphic_decreasing(
            model=german_credit_model,
            dataset=german_credit_test_data,
            transformation_function=perturbation,
            threshold=0.5,
            classification_label="random_value",
        ).execute()


def test_metamorphic_increasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):

        @transformation_function()
        def perturbation(x: pd.Series) -> pd.Series:
            x.duration_in_month = x.duration_in_month * 0.5
            return x

        metamorphic.test_metamorphic_increasing(
            model=german_credit_model,
            dataset=german_credit_test_data,
            transformation_function=perturbation,
            threshold=0.5,
            classification_label="random_value",
        ).execute()


def test_metamorphic_increasing_t_test(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_increasing_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_t_test(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_decreasing_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_wilcoxon(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_increasing_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_wilcoxon(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_decreasing_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_t_test_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_increasing_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_t_test_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_decreasing_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_increasing_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_decreasing_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        critical_quantile=0.05,
        classification_label="Default",
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_llm():
    from langchain.chains import LLMChain
    from langchain.llms.fake import FakeListLLM
    from langchain.prompts import PromptTemplate

    responses = [
        "\n\nHueFoots.",
        "\n\nEcoDrive Motors.",
        "\n\nRainbow Socks.",
        "\n\nNoOil Motors.",
    ]
    llm = FakeListLLM(responses=responses)
    prompt = PromptTemplate(
        input_variables=["product"],
        template="What is a good name for a company that makes {product}?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    wrapped_model = giskard.Model(
        chain, model_type="text_generation", name="demo", description="test", feature_names=["product"]
    )
    df = pd.DataFrame(["colorful socks", "electric car"], columns=["product"])

    wrapped_dataset = giskard.Dataset(df, cat_columns=[])

    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x["product"] = f"some {x['product']}"
        return x

    results = metamorphic.test_metamorphic_increasing(
        model=wrapped_model, dataset=wrapped_dataset, transformation_function=perturbation, threshold=0
    ).execute()

    assert results.actual_slices_size[0] == 2
    assert results.passed
