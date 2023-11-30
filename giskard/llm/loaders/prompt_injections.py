import ast
import requests
from typing import Optional
import pandas as pd

from giskard.datasets.base import Dataset

INJECTION_DATA_URL = "https://raw.githubusercontent.com/Giskard-AI/prompt-injections/main/prompt_injections.csv"
GISKARD_META_URL = "https://raw.githubusercontent.com/Giskard-AI/prompt-injections/main/giskard_meta_data.csv"


def _check_url(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        raise ConnectionError(f"A problem occured while trying to connect to {url}")


def _check_matching_dfs_len(df1, df2):
    if df1 is not None and len(df1) != len(df2):
        raise ValueError(
            f"{__name__}: {INJECTION_DATA_URL} and {GISKARD_META_URL} should "
            "have the same length and should be a one-to-one mapping of each other."
        )


class PromptInjectionDataLoader:
    def __init__(
        self,
        num_samples: Optional[int] = None,
    ):
        self.num_samples = num_samples
        self._prompts_df = None
        self._meta_df = None
        self.sampled_idx = None

    def load_dataset(self, features) -> Dataset:
        formatted_df = pd.DataFrame({feature: self.prompts_df.prompt for feature in features})
        return Dataset(
            df=formatted_df,
            name="Injection Prompts",
            target=None,
            cat_columns=None,
            validation=False,
        )

    def _sample_df(self, df):
        if self.num_samples is not None:
            if self.sampled_idx is None:
                df = df.sample(self.num_samples)
                self.sampled_idx = df.index
                df.reset_index(inplace=True, drop=True)
            else:
                df.iloc[self.sampled_idx].reset_index(drop=True)
        return df

    @property
    def prompts_df(self):
        if self._prompts_df is None:
            _check_url(INJECTION_DATA_URL)
            self._prompts_df = pd.read_csv(INJECTION_DATA_URL)
            _check_matching_dfs_len(self._meta_df, self._prompts_df)
            self._prompts_df = self._sample_df(self._prompts_df)
        return self._prompts_df

    @property
    def meta_df(self):
        if self._meta_df is None:
            _check_url(GISKARD_META_URL)
            self._meta_df = pd.read_csv(GISKARD_META_URL)
            _check_matching_dfs_len(self._prompts_df, self._meta_df)
            self._meta_df.substrings = self._meta_df.substrings.apply(ast.literal_eval)
            self._meta_df = self._sample_df(self._meta_df)
        return self._meta_df

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
