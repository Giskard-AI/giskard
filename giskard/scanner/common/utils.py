from ...datasets.base import Dataset
from ...models.base import BaseModel


def get_dataset_subsample(dataset: Dataset, model: BaseModel, max_data_size: int):
    if max_data_size <= 0 or len(dataset) <= max_data_size:  # just double checking
        return dataset
    if not model.is_classification:
        return dataset.slice(lambda df: df.sample(max_data_size, random_state=42), row_level=False)

    # Slice the dataset while keeping the class proportions
    keep_ratio = max_data_size / len(dataset)
    dataset = dataset.slice(
        lambda df: df.groupby(dataset.target, group_keys=False, sort=False).sample(frac=keep_ratio, random_state=42),
        row_level=False,
    )
    return dataset
