from giskard.core.suite import Suite
from giskard.scanner.performance.issues import PerformanceIssue, PerformanceIssueInfo
from giskard.scanner.performance.metrics import Accuracy
from giskard.scanner.report import ScanReport


def test_generate_test_suite_from_scan_result(german_credit_data, german_credit_model):
    issues = [
        PerformanceIssue(
            german_credit_model,
            german_credit_data,
            level="major",
            info=PerformanceIssueInfo(
                metric=Accuracy(),
                metric_value_reference=0.8,
                metric_value_slice=0.5,
                slice_fn=lambda x: True,
                slice_size=100,
                threshold=0.1,
            ),
        )
    ]
    result = ScanReport(issues)
    test_suite = result.generate_test_suite("Custom name")

    assert isinstance(test_suite, Suite)
    assert test_suite.name == "Custom name"
    assert len(test_suite.tests) == 1

    test_suite.run()
