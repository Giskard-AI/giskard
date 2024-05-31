# For the complete tutorial, check: https://huggingface.co/docs/transformers/tasks/sequence_classification
import pandas as pd
import pytest
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from giskard import Dataset
from giskard.models.huggingface import HuggingFaceModel

tf = pytest.importorskip("tensorflow")


@pytest.mark.memory_expensive
def test_sequence_classification_distilbert_base_uncased_tensorflow():
    tokenizer_distilbert_base_uncased = AutoTokenizer.from_pretrained("stevhliu/my_awesome_model")

    id2label = {0: "NEGATIVE", 1: "POSITIVE"}
    label2id = {"NEGATIVE": 0, "POSITIVE": 1}

    model_distilbert_base_uncased = TFAutoModelForSequenceClassification.from_pretrained(
        "stevhliu/my_awesome_model", num_labels=2, id2label=id2label, label2id=label2id
    )

    text = "This was a masterpiece. Not completely faithful to the books, but enthralling from beginning to end. Might be my favorite of the three."

    raw_data = {
        "text": text,
        "label": "POSITIVE",
    }
    test_df = pd.DataFrame(raw_data, columns=["text", "label"], index=[0])
    feature_names = ["text"]

    def my_preproccessing_function(df):
        return tokenizer_distilbert_base_uncased(list(df["text"]), return_tensors="tf")

    my_model = HuggingFaceModel(
        name="stevhliu/my_awesome_model",
        model=model_distilbert_base_uncased,
        feature_names=feature_names,
        model_type="classification",
        classification_labels=list(label2id.keys()),
        data_preprocessing_function=my_preproccessing_function,
    )

    my_test_dataset = Dataset(test_df, name="test dataset", target="label")

    my_model.predict(my_test_dataset)
    # TODO: add assertions
