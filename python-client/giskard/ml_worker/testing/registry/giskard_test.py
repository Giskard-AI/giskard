from typing import Union

from giskard.ml_worker.core.test_result import TestResult


class GiskardTest:
    """
    The base class of all Giskard's tests

    The test are then executed inside the execute method
    All arguments shall be passed in the __init__ method
    It is advised to set default value for all arguments (None or actual value) in order to allow autocomplete
    """

    def execute(self) -> Union[bool, TestResult]:
        """
        Execute the test
        :return: A SingleTestResult containing detailed information of the test execution results
        """
        pass
