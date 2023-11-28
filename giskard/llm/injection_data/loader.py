import os
import ast
from typing import Optional
import pandas as pd
from pathlib import Path

from giskard.datasets.base import Dataset


INJECTION_DATA_FILENAME = "injection_prompts_data.csv"
GISKARD_META_FILENAME = "giskard_meta_data.csv"


class PromptInjectionDataLoader:
    def __init__(
        self,
        local_path: str = os.path.dirname(__file__),
        num_samples: Optional[int] = None,
    ):

        data_path = Path(local_path) / INJECTION_DATA_FILENAME
        meta_path = Path(local_path) / GISKARD_META_FILENAME

        for path in [local_path, data_path, meta_path]:
            if not os.path.exists(path):
                raise ValueError(f"{self.__class__.__name__}: {path} does not exist")

        self.prompts_df = pd.read_csv(data_path)
        self.meta_df = pd.read_csv(meta_path)

        if len(self.prompts_df) != len(self.meta_df):
            raise ValueError(
                f"{self.__class__.__name__}: {INJECTION_DATA_FILENAME} and {GISKARD_META_FILENAME} should "
                "have the same length and should be a one-to-one mapping of each other."
            )

        self.meta_df.substrings = self.meta_df.substrings.apply(ast.literal_eval)
        if num_samples is not None:
            self.prompts_df = self.prompts_df.sample(num_samples)
            idx_list = self.prompts_df.index
            self.prompts_df.reset_index(inplace=True, drop=True)
            self.meta_df = self.meta_df.iloc[idx_list].reset_index(drop=True)

    def load_dataset(self, features) -> Dataset:
        formatted_df = pd.DataFrame({feature: self.prompts_df.prompt for feature in features})
        return Dataset(
            df=formatted_df,
            name="Injection Prompts",
            target=None,
            cat_columns=None,
            validation=False,
        )

    @property
    def names(self):
        return self.prompts_df.name.tolist()

    @property
    def groups(self):
        return self.prompts_df.group.tolist()

    @property
    def groups_mapping(self):
        return self.meta_df.group_mapping.tolist()

    @property
    def all_meta_df(self):
        additional_meta = self.prompts_df.drop("prompt", axis=1)
        return pd.concat([self.meta_df, additional_meta], axis=1)
