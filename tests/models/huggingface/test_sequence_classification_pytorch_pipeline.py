# For the complete tutorial, check: https://huggingface.co/docs/transformers/tasks/sequence_classification
import pandas as pd
import pytest
from transformers import pipeline

from giskard import Dataset
from giskard.models.huggingface import HuggingFaceModel


@pytest.mark.memory_expensive
def test_sequence_classification_distilbert_base_uncased_pytorch_pipeline():
    text = "This was a masterpiece. Not completely faithful to the books, but enthralling from beginning to end. Might be my favorite of the three."

    my_classifier = pipeline(task="sentiment-analysis", model="stevhliu/my_awesome_model")

    # The labels do not seem to correctly configured for "stevhliu/my_awesome_model" so we're using here the default
    # labels provided by pipeline
    label2id = {"LABEL_0": 0, "LABEL_1": 1}

    raw_data = {
        "text": text,
        "label": "LABEL_1",
    }
    test_df = pd.DataFrame(raw_data, columns=["text", "label"], index=[0])

    feature_names = ["text"]

    def my_preproccessing_function(df):
        return df["text"].tolist()

    my_model = HuggingFaceModel(
        name="stevhliu/my_awesome_model",
        model=my_classifier,
        feature_names=feature_names,
        model_type="classification",
        classification_labels=list(label2id.keys()),
        data_preprocessing_function=my_preproccessing_function,
    )

    my_test_dataset = Dataset(test_df, name="test dataset", target="label")

    predictions = my_model.predict(my_test_dataset).prediction
    assert list(my_test_dataset.df["label"]) == list(predictions)

    # Try with multiple samples
    text2 = "Give me a label 0!"
    raw_data = {
        "text": [text, text2, text],
        "label": ["LABEL_1", "LABEL_0", "LABEL_1"],
    }
    test_df = pd.DataFrame(raw_data, columns=["text", "label"])
    my_test_dataset = Dataset(test_df, name="test dataset", target="label")

    predictions = my_model.predict(my_test_dataset).prediction
    assert list(my_test_dataset.df["label"]) == list(predictions)
