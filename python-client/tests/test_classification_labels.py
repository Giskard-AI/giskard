import warnings

from giskard.models.automodel import Model
from giskard.core.model_validation import validate_model
import numpy as np
import pytest


def validate_ModelPredictionResults(prediction, classification_labels):
    assert np.allclose(np.array(prediction.raw[0]), np.array([0.04886505, 0.95113495]))
    assert np.array_equal(prediction.prediction, np.array(['Not default', 'Default', 'Not default',
                                                           'Default', 'Default']))
    assert np.allclose(np.array(prediction.raw_prediction), np.array([1, 0, 1, 0, 0]))
    assert np.allclose(np.array(prediction.probabilities[0]), np.array([0.95113495]))
    assert np.array_equal(prediction.all_predictions.columns, classification_labels)


@pytest.mark.parametrize(
    "data,model", [("german_credit_data", "german_credit_raw_model")]
)
def test_classification_labels_default(model, data, request):
    gsk_dataset = request.getfixturevalue(data)
    clf = request.getfixturevalue(model)

    classification_labels = clf.classes_

    my_model = Model(
        model=clf,
        model_type="classification",
        classification_labels=classification_labels,
    )

    gsk_dataset.df = gsk_dataset.df.head()
    prediction = my_model.predict(gsk_dataset)
    validate_ModelPredictionResults(prediction, classification_labels)


@pytest.mark.parametrize(
    "data,model", [("german_credit_data", "german_credit_raw_model")]
)
def test_classification_labels_new(model, data, request):
    gsk_dataset = request.getfixturevalue(data)
    clf = request.getfixturevalue(model)

    classification_labels = {0: "Default", 1: "Not default"}
    _classification_labels = {"Default": 0, "Not default": 1}

    my_model = Model(
        model=clf,
        model_type="classification",
        classification_labels=classification_labels,
    )

    gsk_dataset.df[gsk_dataset.target] = gsk_dataset.df[gsk_dataset.target].apply(lambda x: _classification_labels[x])
    gsk_dataset.df = gsk_dataset.df.head()
    prediction = my_model.predict(gsk_dataset)
    validate_ModelPredictionResults(prediction, list(classification_labels.values()))


@pytest.mark.parametrize(
    "data,model", [("german_credit_data", "german_credit_raw_model")]
)
def test_classification_warning(model, data, request):
    gsk_dataset = request.getfixturevalue(data)
    clf = request.getfixturevalue(model)

    classification_labels = [0, 1]
    _classification_labels = {"Default": 0, "Not default": 1}

    my_model = Model(
        model=clf,
        model_type="classification",
        classification_labels=classification_labels,
    )

    gsk_dataset.df[gsk_dataset.target] = gsk_dataset.df[gsk_dataset.target].apply(lambda x: _classification_labels[x])
    gsk_dataset.df = gsk_dataset.df.head()

    with pytest.warns(
            UserWarning,
            match=r"Hint: .*",
    ):
        validate_model(model=my_model, validate_ds=gsk_dataset)
