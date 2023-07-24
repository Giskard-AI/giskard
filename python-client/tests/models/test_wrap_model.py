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
