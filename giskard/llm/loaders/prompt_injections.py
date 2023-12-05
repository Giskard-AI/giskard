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
    if len(df1) != len(df2):
        raise ValueError(
            f"{__name__}: {INJECTION_DATA_URL} and {GISKARD_META_URL} should "
            "have the same length and should be a one-to-one mapping of each other."
        )


def _check_meta_df_requirements(df):
    if "substrings" not in df.columns:
        raise ValueError(f"{__name__}: substrings are needed for the evaluation.")

    if df.substrings.isnull().values.any():
        raise ValueError(f"{__name__}: substrings column cannot have any NaN values.")
    df.substrings = df.substrings.apply(ast.literal_eval)


class PromptInjectionDataLoader:
    def __init__(
        self,
        num_samples: Optional[int] = None,
    ):
        self.num_samples = num_samples
        self._df = None

    def load_dataset_from_group(self, features, group) -> Dataset:
        prompts = self.prompts_from_group(group)
        prompts = pd.DataFrame({feature: prompts for feature in features}, index=prompts.index)
        return Dataset(
            df=prompts,
            name="Injection Prompts",
            target=None,
            cat_columns=None,
            validation=False,
        )

    @property
    def df(self):
        if self._df is None:
            _check_url(INJECTION_DATA_URL)
            _check_url(GISKARD_META_URL)
            prompt_injections_df = pd.read_csv(INJECTION_DATA_URL, index_col=["index"])
            meta_df = pd.read_csv(GISKARD_META_URL, index_col=["index"])
            _check_matching_dfs_len(meta_df, prompt_injections_df)
            _check_meta_df_requirements(meta_df)
            self._df = prompt_injections_df.join(meta_df)

            if self.num_samples is not None:
                self._df = self._df.sample(self.num_samples)
                self._df.reset_index(inplace=True, drop=True)

        return self._df

    @property
    def names(self):
        return self.df.name.tolist()

    @property
    def groups(self):
        return list(set(self.df.group_mapping.tolist()))

    def df_from_group(self, group):
        return self.df.loc[self.df["group_mapping"] == group]

    def prompts_from_group(self, group):
        return self.df_from_group(group).prompt

    def config_df_from_group(self, group):
        return self.df_from_group(group).drop(["prompt"], axis=1)

    def group_description(self, group):
        group_description = self.df_from_group(group).description.to_list()
        if len(set(group_description)) != 1:
            raise ValueError(f"{self.__class__.__name__}: There must be only one group description per group.")
        return group_description[0]

    def group_deviation_description(self, group):
        group_deviation_description = self.df_from_group(group).deviation_description.to_list()
        if len(set(group_deviation_description)) != 1:
            raise ValueError(
                f"{self.__class__.__name__}: There must be only one group description deviation per group."
            )
        return group_deviation_description[0]
