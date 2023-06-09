import os
import re
import string
import random
from typing import Union, List
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

from giskard import Dataset, Model
from tests.url_utils import fetch_from_ftp


# Data
DATA_URL = os.path.join("ftp://sys.giskard.ai", "pub", "unit_test_resources", "tripadvisor_reviews_dataset", "{}")
DATA_PATH = Path.home() / ".giskard" / "tripadvisor_reviews_dataset"
DATA_FILE_NAME = "tripadvisor_hotel_reviews.csv"

# Constants
PRETRAINED_WEIGHTS_NAME = "distilbert-base-uncased"
TEXT_COLUMN_NAME = "Review"
TARGET_COLUMN_NAME = "label"
RANDOM_SEED = 0
MAX_NUM_ROWS = 500


def create_label(x: int) -> int:
    """Map rating to the label."""
    if x in [1, 2]:
        return 0
    if x == 3:
        return 1
    if x in [4, 5]:
        return 2


class TextCleaner:
    """Helper class to preprocess review's text."""

    def __init__(self, clean_pattern: str = r"[^A-ZĞÜŞİÖÇIa-zğüı'şöç0-9.\"',()]"):
        """Constructor of the class."""
        self.clean_pattern = clean_pattern

    def __call__(self, text: Union[str, list]) -> List[List[str]]:
        """Perform cleaning."""
        if isinstance(text, str):
            docs = [[text]]

        if isinstance(text, list):
            docs = text

        text = [[re.sub(self.clean_pattern, " ", sentence) for sentence in sentences] for sentences in docs]
        return text


def remove_emoji(data: str) -> str:
    """Remove emoji from the text."""
    emoji = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        re.UNICODE,
    )
    return re.sub(emoji, "", data)


regex = re.compile("[%s]" % re.escape(string.punctuation))


def remove_punctuation(text: str) -> str:
    """Remove punctuation from the text."""
    text = regex.sub(" ", text)
    return text


def text_preprocessor(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess text."""
    text_cleaner = TextCleaner()

    # Remove emoji.
    df[TEXT_COLUMN_NAME] = df[TEXT_COLUMN_NAME].apply(lambda x: remove_emoji(x))

    # Lower.
    df[TEXT_COLUMN_NAME] = df[TEXT_COLUMN_NAME].apply(lambda x: x.lower())

    # Clean.
    df[TEXT_COLUMN_NAME] = df[TEXT_COLUMN_NAME].apply(lambda x: text_cleaner(x)[0][0])

    # Remove punctuation.
    df[TEXT_COLUMN_NAME] = df[TEXT_COLUMN_NAME].apply(lambda x: remove_punctuation(x))

    return df


def load_dataset() -> pd.DataFrame:
    # Download dataset
    fetch_from_ftp(DATA_URL.format(DATA_FILE_NAME), DATA_PATH / DATA_FILE_NAME)
    df = pd.read_csv(DATA_PATH / DATA_FILE_NAME, nrows=MAX_NUM_ROWS)
    # Obtain labels for our task.
    df[TARGET_COLUMN_NAME] = df.Rating.apply(lambda x: create_label(x))
    df.drop(columns="Rating", inplace=True)
    df = text_preprocessor(df)
    return df


@dataclass
class Config:
    """Configuration of Distill-BERT model."""

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    batch_size = 128
    seq_length = 150
    add_special_tokens = True
    return_attention_mask = True
    pad_to_max_length = True
    return_tensors = "pt"


def create_dataloader(df: pd.DataFrame) -> DataLoader:
    """Create dataloader object with input data."""

    def _create_dataset(encoded_data: dict) -> TensorDataset:
        """Create dataset object with input data."""
        input_ids = encoded_data["input_ids"]
        attention_masks = encoded_data["attention_mask"]
        return TensorDataset(input_ids, attention_masks)

    # Load tokenizer.
    tokenizer = DistilBertTokenizer.from_pretrained(PRETRAINED_WEIGHTS_NAME)

    # Tokenize data.
    encoded_data = tokenizer.batch_encode_plus(
        df.Review.values,
        add_special_tokens=Config.add_special_tokens,
        return_attention_mask=Config.return_attention_mask,
        pad_to_max_length=Config.pad_to_max_length,
        max_length=Config.seq_length,
        return_tensors=Config.return_tensors,
    )

    # Create dataset object.
    dataset = _create_dataset(encoded_data)

    # Create and return dataloader object.
    return DataLoader(dataset, batch_size=Config.batch_size)


def infer_predictions(_model: torch.nn.Module, _dataloader: DataLoader) -> np.ndarray:
    """Perform inference using given model on given dataloader."""
    _model.eval()

    y_pred = list()
    for batch in _dataloader:
        batch = tuple(b.to(Config.device) for b in batch)
        inputs = {"input_ids": batch[0], "attention_mask": batch[1]}

        with torch.no_grad():
            outputs = _model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits).detach().cpu().numpy()
        y_pred.append(probs)

    y_pred = np.concatenate(y_pred, axis=0)
    return y_pred


class CustomWrapper(Model):
    """Custom giskard model wrapper."""

    def model_predict(self, df: pd.DataFrame) -> np.ndarray:
        """Perform inference using overwritten prediction logic."""
        # Set random seed
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        torch.manual_seed(RANDOM_SEED)
        torch.cuda.manual_seed_all(RANDOM_SEED)

        cleaned_df = text_preprocessor(df)
        data_loader = create_dataloader(cleaned_df)
        predicted_probabilities = infer_predictions(self.model, data_loader)
        return predicted_probabilities


@pytest.fixture()
def tripadvisor_data() -> Dataset:
    # Download dataset
    df = load_dataset()
    return Dataset(
        df, name="trip_advisor_reviews_sentiment", target=TARGET_COLUMN_NAME, column_types={TEXT_COLUMN_NAME: "text"}
    )


@pytest.fixture()
def tripadvisor_model(tripadvisor_data: Dataset) -> Model:
    # Load model.
    model = DistilBertForSequenceClassification.from_pretrained(
        PRETRAINED_WEIGHTS_NAME, num_labels=3, output_attentions=False, output_hidden_states=False
    ).to(Config.device)

    return CustomWrapper(
        model,
        model_type="classification",
        classification_labels=[0, 1, 2],
        name="trip_advisor_sentiment_classifier",
        feature_names=[TEXT_COLUMN_NAME],
    )
