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
        model=DummyClassifier(strategy="constant", constant=1).fit(data, np.ones(len(data))),
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


def test_validate_columns_columntypes(german_credit_data, german_credit_test_data):
    with pytest.warns(UserWarning,
                      match=r"Feature 'people_under_maintenance' is declared as 'numeric' but has 2 .* Are you sure it is not a 'category' feature?"):
        validate_column_categorization(
            german_credit_test_data.df,
            german_credit_test_data.feature_types
        )
    validate_column_categorization(
        german_credit_test_data.df,
        {c: german_credit_test_data.feature_types[c] for c in german_credit_test_data.feature_types if
         c != german_credit_test_data.target}
    )
    validate_column_categorization(
        german_credit_test_data.df,
        german_credit_test_data.feature_types
    )
    with pytest.raises(ValueError) as e:
        validate_columns_columntypes(
            german_credit_data.df,
            {c: german_credit_data.feature_types[c] for c in german_credit_data.feature_types if
             c not in {german_credit_data.target, "sex"}},
            german_credit_data.target
        )
    assert e.match(r"Invalid column_types parameter: Please declare the type for {'sex'} columns")

    with pytest.raises(ValueError) as e:
        new_ct = dict(german_credit_data.feature_types)
        new_ct["non-existing-column"] = "int64"
        validate_columns_columntypes(
            german_credit_data.df,
            new_ct,
            german_credit_data.target
        )
    assert e.match(r"Missing columns in dataframe according to column_types: {'non-existing-column'}")

    broken_types = dict(german_credit_test_data.feature_types)
    broken_types['people_under_maintenance'] = SupportedColumnType.CATEGORY.value
    broken_types['sex'] = SupportedColumnType.NUMERIC.value
    with pytest.warns(UserWarning,
                      match=r"Feature 'sex' is declared as 'numeric' but has 2 .* Are you sure it is not a 'category' feature?") as w:
        validate_column_categorization(
            german_credit_test_data.df,
            broken_types
        )
