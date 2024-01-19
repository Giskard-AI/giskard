from .. import Dataset, Suite
from ..testing.tests.llm import test_llm_correctness


class TestSet(Dataset):
    """A wrapper class around `Dataset` to allow automatic creation
    of a `Suite` based on the question/answer pairs inside the `TestSet`.
    """

    def to_test_suite(self):
        suite_default_params = {"dataset": self}
        suite = Suite(name="Test suite generated from testset", default_params=suite_default_params)
        suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        return suite
