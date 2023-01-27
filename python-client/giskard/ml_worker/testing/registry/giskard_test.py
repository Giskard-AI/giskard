from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult


class GiskardTest:
    """
    The base class of all Giskard's tests

    The test are then executed inside the execute method
    All arguments shall be passed in the __init__ method
    It is advised to set default value for all arguments (None or actual value) in order to allow autocomplete
    """
    def execute(self) -> SingleTestResult:
        """
        Execute the test
        :return: A SingleTestResult containing detailed information of the test execution results
        """
        pass


