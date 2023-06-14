import pytest
from scipy import special
from transformers import BertTokenizer, BertForSequenceClassification

import tests.utils
from giskard import Dataset
from giskard.models.huggingface import HuggingFaceModel


def my_softmax(x):
    return special.softmax(x, axis=1)


@pytest.mark.parametrize("dataset_name", ["enron_data_full"])
def test_email_classification_bert_custom_model(dataset_name, request):
    data_filtered = request.getfixturevalue(dataset_name).df

    # Exclude target category with very few rows ; 812 rows remains
    excluded_category = [
        "talking points",
        "meeting minutes",
        "trip reports",
    ]
    data_filtered = data_filtered[-data_filtered["Target"].isin(excluded_category)]

    # Define pretrained tokenizer and model
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2"

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    for param in model.base_model.parameters():
        param.requires_grad = False

    classification_labels_mapping = {"REGULATION": 0, "INTERNAL": 1, "CALIFORNIA CRISIS": 2, "INFLUENCE": 3}

    def preprocessing_func(test_dataset):
        test_dataset = test_dataset.squeeze(axis=1)
        X_test = list(test_dataset)
        X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512, return_tensors="pt")
        return X_test_tokenized

    my_model = HuggingFaceModel(
        name=model_name,
        model=model,
        feature_names=["Content"],
        model_type="classification",
        classification_labels=list(classification_labels_mapping.keys()),
        data_preprocessing_function=preprocessing_func,
    )

    my_test_dataset = Dataset(
        data_filtered.head(5), name="test dataset", target="Target", cat_columns=["Week_day", "Month"]
    )

    tests.utils.verify_model_upload(my_model, my_test_dataset)
