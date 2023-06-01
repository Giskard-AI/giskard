import tempfile
from typing import *

import numpy as np
import pandas as pd

from giskard.client.python_utils import warning
from giskard.core.core import SupportedModelTypes, SupportedFeatureTypes
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset


def validate_target(target, dataframe_keys):
    if target not in dataframe_keys:
        raise ValueError(
            f"Invalid target parameter:"
            f" {target} column is not present in the dataset with columns: {dataframe_keys}"
        )


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"


