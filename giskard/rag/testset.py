from typing import Optional, Sequence

import json

import pandas as pd

from ..core.suite import Suite
from ..datasets.base import Dataset
from ..testing.tests.llm import test_llm_correctness


class QATestset:
    """A class to represent a testset for QA models."""

    def __init__(self, dataframe: pd.DataFrame):
        self._dataframe = dataframe

    def __len__(self):
        return len(self._dataframe)

    def to_pandas(self, filters: Optional[dict] = None):
        """Return the testset as a pandas DataFrame.

        Parameters
        ----------
        filters : dict, optional
            A dictionary of filters to apply to the testset. The keys are the metadata names and the values are list of kept values.
            If multiple metadata are provided, the filters are combined with an AND operator.

        """

        if filters is not None:
            return self._dataframe[
                self._dataframe["metadata"].apply(lambda x: all(x.get(k) in v for k, v in filters.items()))
            ]
        return self._dataframe

    def to_dataset(self, filters: Optional[dict] = None):
        dataframe = self.to_pandas(filters=filters).copy()
        dataframe["conversation_history"] = dataframe["conversation_history"].apply(lambda x: json.dumps(x))
        dataframe["metadata"] = dataframe["metadata"].apply(lambda x: json.dumps(x))
        return Dataset(dataframe, name="QA Testset", target=False, validation=False)

    def get_metadata_values(self, metadata_name: str):
        """Return the unique values of a metadata field."""
        metadata_values = list(
            set([metadata[metadata_name] for metadata in self._dataframe["metadata"] if metadata_name in metadata])
        )
        metadata_values.sort()
        return metadata_values

    def count_sample_by_metadata(self, metadata_name: str):
        """Count the number of samples for each value of a metadata field."""
        return self._dataframe["metadata"].apply(lambda x: x.get(metadata_name)).value_counts()

    def save(self, path):
        """Save the testset as a JSONL file.

        Parameters
        ----------
        path : str
            The path to the output JSONL file.
        """
        self._dataframe.reset_index().to_json(path, orient="records", lines=True)

    @classmethod
    def load(cls, path):
        """Load a testset from a JSONL file.

        Parameters
        ----------
        path : str
            The path to the input JSONL file.
        """
        dataframe = pd.read_json(path, orient="records", lines=True).set_index("id")
        dataframe.index = dataframe.index.astype(str)
        return cls(dataframe)

    def to_test_suite(self, name=None, slicing_metadata: Optional[Sequence[str]] = None):
        """
        Convert the testset to a Giskard test suite.

        Parameters
        ----------
        name : str, optional
            The name of the test suite. If not provided, the name will be "Test suite generated from testset".

        Returns
        -------
        giskard.Suite
            The test suite.
        """

        if slicing_metadata is None:
            suite_default_params = {"dataset": self.to_dataset()}
            name = name or "Test suite generated from testset"
            suite = Suite(name=name, default_params=suite_default_params)
            suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        else:
            name = name or "Test suite generated from testset"
            suite = Suite(name=name)
            for metadata_name in slicing_metadata:
                metadata_values = self.get_metadata_values(metadata_name)
                for value in metadata_values:
                    suite.add_test(
                        test_llm_correctness(dataset=self.to_dataset(filters={metadata_name: [value]})),
                        f"TestsetCorrectnessTest_{metadata_name}_{value}",
                        f"TestsetCorrectnessTest_{metadata_name}_{value}",
                    )
        return suite

    def copy(self):
        """Return a copy of the testset."""
        return QATestset(self._dataframe.copy())

    @property
    def samples(self):
        return self._dataframe.loc[:, ("question", "conversation_history")].to_dict(orient="records")
