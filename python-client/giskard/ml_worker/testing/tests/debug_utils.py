import copy
import uuid
from giskard import Dataset

try:
    import catalogue
except ImportError as e:
    raise ImportError("Please install it via 'pip install catalogue'") from e

slices_to_debug = catalogue.create("giskard", "slices_to_debug")


def fresh_copy(gsk_dataset: Dataset, suffix="_copy"):
    copied_dataset = copy.deepcopy(gsk_dataset)
    copied_dataset.uuid = uuid.uuid4()
    copied_dataset.name = copied_dataset.name + suffix if copied_dataset.name else suffix
    return copied_dataset


@slices_to_debug.register("_test_classification_score")
def _test_classification_score(gsk_dataset: Dataset, predictions):
    sliced_dataset = fresh_copy(gsk_dataset)
    if hasattr(gsk_dataset, "df"):  # tabular and NLP cases
        targets = gsk_dataset.df[gsk_dataset.target].astype(str)
        sliced_dataset.df = sliced_dataset.df.loc[targets != predictions]
        return sliced_dataset
