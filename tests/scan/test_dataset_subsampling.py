import numpy as np
import pandas as pd

from giskard import Dataset, Model
from giskard.scanner.common.utils import get_dataset_subsample


def test_get_dataset_subsample():
    # Create dummy dataset with 20% of samples having label 1, 20% label 2, and the rest label 0
    data = {"feature": np.arange(1000), "target": np.zeros(1000)}
    data["target"][0:200] = 1
    data["target"][200:400] = 2
    np.random.shuffle(data["target"])
    df = pd.DataFrame(data)
    dataset = Dataset(df, target="target")

    # Create dummy model
    model = Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1, 2])

    # Test new dataset size
    max_data_size = len(dataset) // 10
    result = get_dataset_subsample(dataset, model, max_data_size)
    assert len(result) == max_data_size

    # For each label, check that the proportion of samples is preserved
    label_counts = dataset.df.target.value_counts()
    for label in label_counts.index:
        assert result.df.target.tolist().count(label) == label_counts[label] // 10

    # Edge case: max size larger than original size (should return the original dataset)
    large_max_data_size = len(dataset) * 2
    result_large = get_dataset_subsample(dataset, model, large_max_data_size)
    assert len(result_large) == len(dataset)

    # Edge case: max size 0 (should return the original dataset)
    result_zero = get_dataset_subsample(dataset, model, 0)
    assert len(result_zero) == len(dataset)
