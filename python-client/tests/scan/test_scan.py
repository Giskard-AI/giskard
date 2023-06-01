from giskard.scanner.performance.performance_scan import PerformanceScan


def test_scan(german_credit_data, german_credit_model):
    assert PerformanceScan(metrics=["f1"]).run(german_credit_model, german_credit_data)
