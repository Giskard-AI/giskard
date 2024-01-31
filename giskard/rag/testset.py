from .. import Dataset, Suite
from ..testing.tests.llm import test_llm_correctness


class QATestset(Dataset):
    """A wrapper class around `Dataset` to allow automatic creation
    of a `Suite` based on the question/answer pairs inside the `TestSet`.
    """

    def to_test_suite(self, name=None):
        suite_default_params = {"dataset": self}
        name = name or "Test suite generated from testset"
        suite = Suite(name=name, default_params=suite_default_params)
        suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        return suite

    def copy(self):
        testset = QATestset(
            df=self.df.copy(),
            target=self.target,
            column_types=self.column_types.copy(),
            validation=False,
        )

        if hasattr(self, "column_meta"):
            testset.load_metadata_from_instance(self.column_meta)
        return testset
