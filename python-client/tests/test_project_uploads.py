import warnings

import pytest
from sklearn.dummy import DummyClassifier

from giskard.core.dataset_validation import *
from giskard.core.model import ModelPredictionResults
from giskard.core.model_validation import *
from giskard.models.sklearn import SKLearnModel

data = np.array(["g", "e", "e", "k", "s"])


@pytest.mark.parametrize('pred', [
    [[0.81, 0.32]],
    [[0.9, 0.21]],
    [[1.5, 1]],
    [[-1, 2]],
    [[0.9, -0.1]],
    [[0, -1], [0.8, 0.5]]
])
def test__validate_classification_prediction_warn(pred):
    with pytest.warns():
        validate_classification_prediction(['one', 'two'],
                                           np.array(pred))


@pytest.mark.parametrize('pred', [
    [[0.1, 0.2, 0.7]],
])
def test__validate_classification_prediction_fail(pred):
    with pytest.raises(ValueError):
        validate_classification_prediction(["one", "two"], np.array(pred))


@pytest.mark.parametrize("pred", [[[0, 1]], [[0.999999999999999, 0.000000000000001]]])
def test__validate_classification_prediction_pass(pred):
    validate_classification_prediction(["one", "two"], np.array(pred))


@pytest.mark.parametrize("data", [pd.Series(data)])
def test_verify_is_pandasdataframe_fail(data):
    with pytest.raises(AssertionError):
        validate_is_pandasdataframe(data)


@pytest.mark.parametrize("data", [pd.DataFrame(data)])
def test_verify_is_pandasdataframe_pass(data):
    validate_is_pandasdataframe(data)


def test_validate_deterministic_model():
    data = pd.DataFrame(np.random.rand(5, 1))
    ones = np.ones(len(data))
    constant_model = SKLearnModel(
        clf=DummyClassifier(strategy="constant", constant=1).fit(data, np.ones(len(data))),
        model_type=SupportedModelTypes.CLASSIFICATION
    )
    ds = Dataset(df=data)

    with pytest.warns():
        validate_deterministic_model(constant_model, ds, ModelPredictionResults(raw=ones * 0.5))

    # Make sure there's no warning in other cases
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        validate_deterministic_model(constant_model, ds, constant_model.predict(ds))
        validate_deterministic_model(constant_model, ds, ModelPredictionResults(raw=ones * 0.99999))


def test_validate_column_meanings(german_credit_data, german_credit_test_data):
    test_ds = german_credit_test_data
    ds = german_credit_data

    with pytest.warns(UserWarning,
                      match=r"Feature 'people_under_maintenance' is declared as 'numeric' but has 2 .* Are you sure it is not a 'category' feature?"):
        validate_column_categorization(test_ds)

    test_ds.column_meanings = {c: test_ds.column_meanings[c] for c in test_ds.column_meanings if c != test_ds.target}
    validate_column_categorization(ds)
    original_column_meanings = ds.column_meanings

    with pytest.raises(ValueError) as e:
        ds.column_meanings = {c: original_column_meanings[c] for c in original_column_meanings if c not in {ds.target, "sex"}}
        validate_column_meanings(ds)
    assert e.match(r"Invalid column_meanings parameter: Please declare the type for {'sex'} columns")

    with pytest.raises(ValueError) as e:
        new_ft = dict(original_column_meanings)
        new_ft["non-existing-column"] = SupportedColumnMeanings.CATEGORY.value
        ds.column_meanings = new_ft
        validate_column_meanings(ds)
    assert e.match(r"Missing columns in dataframe according to column_meanings: {'non-existing-column'}")

    broken_types = dict(test_ds.column_meanings)
    broken_types['people_under_maintenance'] = SupportedColumnMeanings.CATEGORY.value
    broken_types['sex'] = SupportedColumnMeanings.NUMERIC.value
    with pytest.warns(UserWarning,
                      match=r"Feature 'sex' is declared as 'numeric' but has 2 .* Are you sure it is not a 'category' feature?") as w:
        test_ds.column_meanings = broken_types
        validate_column_categorization(test_ds)
