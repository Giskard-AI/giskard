from pathlib import Path

import pytest
from keras.utils import text_dataset_from_directory, get_file

batch_size = 32
seed = 42


@pytest.fixture()
def imdb_data():
    dataset = get_file(
        "aclImdb",
        "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz",
        untar=True,
        cache_dir=Path.home() / ".giskard",
    )

    raw_train_ds = text_dataset_from_directory(
        Path(dataset) / "train", batch_size=batch_size, validation_split=0.2, subset="training", seed=seed
    )
    raw_test_ds = text_dataset_from_directory(Path(dataset) / "test", batch_size=batch_size)
    return raw_train_ds, raw_test_ds
