from giskard.scanner import Scanner
from giskard.scanner.result import ScanResult


def test_scanner_returns_non_empty_scan_result(german_credit_data, german_credit_model):
    scanner = Scanner()
    result = scanner.analyze(german_credit_model, german_credit_data)

    assert isinstance(result, ScanResult)
    assert result.has_issues()
