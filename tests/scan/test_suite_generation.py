from unittest.mock import Mock

from giskard.core.suite import Suite
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.scanner.issues import Issue, IssueLevel, Performance
from giskard.scanner.performance.metrics import Accuracy, MetricResult
from giskard.scanner.performance.performance_bias_detector import _generate_performance_tests
from giskard.scanner.report import ScanReport


def test_generate_test_suite_from_scan_result(german_credit_data, german_credit_model):
    issues = [
        Issue(
            model=german_credit_model,
            dataset=german_credit_data,
            group=Performance,
            level=IssueLevel.MAJOR,
            description="Description",
            meta={
                "metric": "Accuracy",
                "metric_value": 0.2,
                "metric_reference_value": 1.0,
                "slice_metric": MetricResult(Accuracy(), 0.2, 100),
                "reference_metric": MetricResult(Accuracy(), 1, 100),
                "threshold": 0.95,
                "p_value": 1e-6,
            },
            slicing_fn=Mock(SlicingFunction),
            tests=_generate_performance_tests,
        )
    ]
    print(issues[0].generate_tests())
    result = ScanReport(issues)
    test_suite = result.generate_test_suite("Custom name", use_suite_input=False)

    assert isinstance(test_suite, Suite)
    assert test_suite.name == "Custom name"
    assert len(test_suite.tests) == 1

    test_suite.run()

    # Test `use_suite_input` is True, pass model and dataset as suite inputs
    test_suite = result.generate_test_suite("Custom name with suite inputs")

    assert isinstance(test_suite, Suite)
    assert test_suite.name == "Custom name with suite inputs"
    assert len(test_suite.tests) == 1

    test_suite.run(model=german_credit_model, dataset=german_credit_data)

