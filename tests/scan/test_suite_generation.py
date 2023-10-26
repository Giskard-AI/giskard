from giskard import slicing_function
from giskard.core.suite import Suite
from giskard.scanner.issues import Issue, IssueLevel, Performance
from giskard.scanner.performance.metrics import Accuracy, MetricResult
from giskard.scanner.performance.performance_bias_detector import _generate_performance_tests
from giskard.scanner.report import ScanReport


def test_generate_test_suite_from_scan_result(german_credit_data, german_credit_model):
    @slicing_function
    def slice_fn(x):
        return True

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
            slicing_fn=slice_fn,
            tests=_generate_performance_tests,
        )
    ]

    result = ScanReport(issues, model=german_credit_model, dataset=german_credit_data)
    test_suite = result.generate_test_suite("Custom name")

    assert isinstance(test_suite, Suite)
    assert test_suite.name == "Custom name"
    assert len(test_suite.tests) == 1

    test_suite.run()
