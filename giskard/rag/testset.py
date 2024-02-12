import pandas as pd

from ..core.suite import Suite
from ..testing.tests.llm import test_llm_correctness


class QATestset:
    def __init__(self, dataframe: pd.DataFrame):
        self._dataframe = dataframe

    def to_pandas(self):
        return self._dataframe

    def save(self, path):
        self._dataframe.to_json(path, orient="records", lines=True)

    @classmethod
    def load(cls, path):
        dataframe = pd.read_json(path, orient="records", lines=True)
        return cls(dataframe)

    def to_test_suite(self, name=None):
        suite_default_params = {"dataset": self}
        name = name or "Test suite generated from testset"
        suite = Suite(name=name, default_params=suite_default_params)
        suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        return suite

    def copy(self):
        return QATestset(self.dataframe.copy())
