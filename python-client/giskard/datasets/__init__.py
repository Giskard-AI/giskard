from typing import Dict, Optional, List
import pandas as pd
from giskard.datasets.base import Dataset
from giskard.core.validation import configured_validate_arguments


@configured_validate_arguments
def wrap_dataset(dataset: pd.DataFrame,
                 name: Optional[str] = None,
                 target: Optional[str] = None,
                 cat_columns: Optional[List[str]] = None,
                 infer_column_types: Optional[bool] = False,
                 column_types: Optional[Dict[str, str]] = None):
    print("Your 'pandas.DataFrame' dataset is successfully wrapped by Giskard's 'Dataset' wrapper class.")
    return Dataset(dataset,
                   name,
                   target,
                   cat_columns,
                   infer_column_types,
                   column_types)
