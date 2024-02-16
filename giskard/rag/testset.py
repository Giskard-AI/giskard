from typing import Optional, Sequence

from copy import deepcopy

import pandas as pd

from ..core.suite import Suite
from ..datasets.base import Dataset
from ..testing.tests.llm import test_llm_correctness


class QATestset:
    """A class to represent a testset for QA models."""

    def __init__(self, dataframe: pd.DataFrame, metadata: Optional[dict] = None):
        self._dataframe = dataframe
        self._metadata = metadata or {id: {} for id in dataframe.index}
        if any(metadata_id not in dataframe.index for metadata_id in self._metadata):
            raise ValueError("At least one metadata id is not in the dataframe index.")
        if any(dataframe_id not in self._metadata for dataframe_id in dataframe.index):
            raise ValueError("At least one dataframe id is not in the metadata.")

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
        kept_indices = []
        if filters is not None:
            for idx in self._dataframe.index:
                if all(self._metadata[idx][meta] in values for meta, values in filters.items()):
                    kept_indices.append(idx)
            return self._dataframe.loc[kept_indices]
        return self._dataframe

    def to_dataset(self, filters: Optional[dict] = None):
        return Dataset(self.to_pandas(filters=filters), name="QA Testset", target=False, validation=False)

    def get_metadata_values(self, metadata_name: str):
        """Return the unique values of a metadata field."""
        metadata_values = list(
            set([metadata[metadata_name] for _, metadata in self._metadata.items() if metadata_name in metadata])
        )
        metadata_values.sort()
        return metadata_values

    def save(self, path):
        """Save the testset as a JSONL file.

        Parameters
        ----------
        path : str
            The path to the output JSONL file.
        """
        df_with_metadata = self._dataframe.copy()
        df_with_metadata["metadata"] = self._metadata
        df_with_metadata.reset_index().to_json(path, orient="records", lines=True)

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
        metadata = dataframe.to_dict().get("metadata", {})
        del dataframe["metadata"]
        return cls(dataframe, metadata=metadata)

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
        return QATestset(self._dataframe.copy(), metadata=deepcopy(self._metadata))
