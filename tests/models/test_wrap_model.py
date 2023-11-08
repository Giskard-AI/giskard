import pytest
from sklearn.linear_model import LogisticRegression

from giskard.models.automodel import Model
from giskard.models.base import CloudpickleSerializableModel
from tests.fixtures.german_credit_scoring import input_types


def test_Model(german_credit_raw_model):
    my_model = Model(
        german_credit_raw_model.predict_proba,
        model_type="classification",
        feature_names=list(input_types),
        classification_threshold=0.5,
        classification_labels=list(german_credit_raw_model.classes_),
    )

    assert isinstance(my_model, CloudpickleSerializableModel)


def test_bound_method_model():
    base_model = LogisticRegression()
    my_model = Model(
        base_model.predict_proba,
        model_type="classification",
        feature_names=["one", "two"],
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )

    assert isinstance(my_model, CloudpickleSerializableModel)


def test_text_generation_model_needs_name_and_description():
    with pytest.raises(ValueError, match=r"The parameters 'name' and 'description' are required"):
        Model(
            lambda x: ["Hello"] * len(x),
            model_type="text_generation",
            feature_names=["one", "two"],
        )

    with pytest.raises(ValueError, match=r"The parameters 'name' and 'description' are required"):
        Model(
            lambda x: ["Hello"] * len(x),
            name="My name",
            model_type="text_generation",
            feature_names=["one", "two"],
        )

    with pytest.raises(ValueError, match=r"The parameters 'name' and 'description' are required"):
        Model(
            lambda x: ["Hello"] * len(x),
            name="",
            description="My description",
            model_type="text_generation",
            feature_names=["one", "two"],
        )

    with pytest.raises(ValueError, match=r"The parameters 'name' and 'description' are required"):
        Model(
            lambda x: ["Hello"] * len(x),
            name="Hello",
            description="",
            model_type="text_generation",
            feature_names=["one", "two"],
        )

    # Should raise no error
    Model(
        lambda x: ["Hello"] * len(x),
        name="Hello",
        description="This is a model that says hello",
        model_type="text_generation",
        feature_names=["one", "two"],
    )

    # Other models should not require name and description
    Model(
        lambda x: ["Hello"] * len(x),
        model_type="regression",
        feature_names=["one", "two"],
    )


def test_text_generation_model_needs_feature_names():
    with pytest.raises(ValueError, match=r"feature_names"):
        Model(
            lambda x: ["Hello"] * len(x),
            name="Hello",
            description="This is a model that says hello",
            model_type="text_generation",
        )

    # Should raise no error
    Model(
        lambda x: ["Hello"] * len(x),
        name="Hello",
        description="This is a model that says hello",
        model_type="text_generation",
        feature_names=["one", "two"],
    )
