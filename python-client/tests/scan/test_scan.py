from giskard.scanner.performance import PerformanceScan


def test_scan(german_credit_data, german_credit_model):
    assert PerformanceScan(german_credit_model, german_credit_data).run()
