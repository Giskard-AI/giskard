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

    def to_pandas(self):
        """Return the testset as a pandas DataFrame."""
        return self._dataframe

    def to_dataset(self):
        return Dataset(self._dataframe, name="QA Testset", target=False, validation=False)

    def save(self, path):
        """Save the testset as a JSONL file.

        Parameters
        ----------
        path : str
            The path to the output JSONL file.
        """
        self._dataframe.to_json(path, orient="records", lines=True)

    @classmethod
    def load(cls, path):
        """Load a testset from a JSONL file.

        Parameters
        ----------
        path : str
            The path to the input JSONL file.
        """
        dataframe = pd.read_json(path, orient="records", lines=True)
        return cls(dataframe)

    def to_test_suite(self, name=None):
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
        suite_default_params = {"dataset": self.to_dataset()}
        name = name or "Test suite generated from testset"
        suite = Suite(name=name, default_params=suite_default_params)
        suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        return suite

    def copy(self):
        """Return a copy of the testset."""
        return QATestset(self._dataframe.copy())
