import os
from typing import Optional
import pandas as pd
import numpy as np

from ...datasets.base import Dataset
from .base import BaseGenerator


class InjectionDataGenerator(BaseGenerator):
    def __init__(
        self,
        local_path: str = os.path.join(os.path.dirname(__file__), "../injection_data/"),
        num_samples: Optional[int] = None,
    ):
        data_path = os.path.join(local_path, "injection_prompts_data.csv")
        meta_path = os.path.join(local_path, "giskard_meta_data.csv")

        for path in [local_path, data_path, meta_path]:
            if not os.path.exists(path):
                raise ValueError(f"{self.__class__.__name__}: {path} does not exist")

        self.prompts_df = pd.read_csv(data_path)
        self.meta_df = pd.read_csv(meta_path)
        if num_samples is not None:
            rows = np.random.randint(2, size=num_samples).astype("bool")
            self.prompts_df = self.prompts_df[rows].reset_index(inplace=True, drop=True)
            self.meta_df = self.meta_df[rows].reset_index(inplace=True, drop=True)

    def generate_dataset(self, column_types) -> Dataset:
        formatted_df = pd.DataFrame(
            {col: self.prompts_df.prompt for col, col_type in column_types.items() if col_type == "text"}
        )
        return Dataset(
            df=formatted_df,
            name="Injection Prompts",
            target=None,
            cat_columns=None,
            column_types=column_types,
            validation=False,
        )

    @property
    def names(self):
        return self.prompts_df.name.tolist()

    @property
    def groups(self):
        return self.meta_df.group.tolist()

    @property
    def groups_mapping(self):
        return self.meta_df.group_mapping.tolist()

    @property
    def all_meta_df(self):
        additional_meta = self.prompts_df.drop("prompt", axis=1)
        return pd.concat([self.meta_df, additional_meta], axis=1)
