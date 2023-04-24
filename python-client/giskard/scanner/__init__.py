from ..models.base import BaseModel
from ..datasets.base import Dataset
from .performance import PerformanceScan
from ..core.model_validation import validate_model


def scan(model: BaseModel, dataset: Dataset, tests=None, method="tree", threshold=-0.1):
    """
    Scan a model with a dataset.

    Args:
        model (BaseModel):
            A Giskard model object.
        dataset (Dataset):
            A Giskard dataset object.
        tests (list):
            A list of tests to run ("f1", "accuracy", "precision", "recall"). If None, will use default tests for the model type.
        method (str):
            The scan method to use. Can be "tree", "optimized", "multiscale", or "bruteforce".
        threshold (float):
            The threshold to detect low performance. Default is -0.1, meaning that variation of metrics below 10% will be considered relevant.
    """

    validate_model(model=model, validate_ds=dataset)
    analyzer = PerformanceScan(model, dataset, tests)
    return analyzer.run(slicer=method, threshold=threshold)
