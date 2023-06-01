from typing import Dict, Optional, List
import pandas as pd
from giskard.datasets.base import Dataset
from giskard.core.validation import validate_args


@validate_args
def dataset(df: pd.DataFrame,
            name: Optional[str] = None,
            target: Optional[str] = None,
            cat_columns: Optional[List[str]] = None,
            infer_column_types: Optional[bool] = False,
            column_types: Optional[Dict[str, str]] = None):
    return Dataset(df,
                   name,
                   target,
                   cat_columns,
                   infer_column_types,
                   column_types)
