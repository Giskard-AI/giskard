from typing import Optional

import ast
from pathlib import Path, PurePath

import pandas as pd

from ...datasets.base import Dataset
from ..evaluators.string_matcher import StringMatcherConfig

INJECTION_DATA_URL = "https://raw.githubusercontent.com/Giskard-AI/prompt-injections/v0.0.2/prompt_injections.csv"
GISKARD_META_URL = "https://raw.githubusercontent.com/Giskard-AI/prompt-injections/v0.0.2/giskard_meta_data.csv"

LOCAL_INJECTION_DATA_PATH = Path(__file__).parent.joinpath("local", "prompt_injections.csv")
LOCAL_GISKARD_META_PATH = Path(__file__).parent.joinpath("local", "giskard_meta_data.csv")


def from_records_to_configs(records):
    configs = []
    for row in records:
        kwargs = {k: v for k, v in row.items() if k in list(StringMatcherConfig.__annotations__.keys())}
        configs.append(StringMatcherConfig(**kwargs))
    return configs


def _try_download(url: str, local_path: PurePath):
    try:
        return pd.read_csv(url, index_col=["index"])
    except:  # noqa NOSONAR
        return pd.read_csv(local_path, index_col=["index"])


class PromptInjectionDataLoader:
    def __init__(
        self,
        num_samples: Optional[int] = None,
        injection_data_url: str = INJECTION_DATA_URL,
        giskard_meta_url: str = GISKARD_META_URL,
    ):
        self.num_samples = num_samples
        self._df = None
        self.injection_data_url = injection_data_url
        self.giskard_meta_url = giskard_meta_url

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
            prompt_injections_df = _try_download(self.injection_data_url, LOCAL_INJECTION_DATA_PATH)
            meta_df = _try_download(self.giskard_meta_url, LOCAL_GISKARD_META_PATH)
            meta_df.expected_strings = meta_df.expected_strings.apply(ast.literal_eval)
            self._df = prompt_injections_df.join(meta_df)

            if self.num_samples is not None:
                self._df = self._df.sample(self.num_samples)

        return self._df

    @property
    def names(self):
        return self.df.name.tolist()

    @property
    def groups(self):
        return self.df.group_mapping.unique().tolist()

    def df_from_group(self, group):
        return self.df.loc[self.df["group_mapping"] == group]

    def prompts_from_group(self, group):
        return self.df_from_group(group).prompt

    def configs_from_group(self, group):
        configs_records = self.df_from_group(group).drop(["prompt"], axis=1).to_dict("records")
        return from_records_to_configs(configs_records)

    def group_description(self, group):
        group_description = self.df_from_group(group).description.to_list()
        return group_description[0]

    def group_deviation_description(self, group):
        group_deviation_description = self.df_from_group(group).deviation_description.to_list()
        return group_deviation_description[0]
