from unittest import mock

import pytest

from giskard import Dataset
from giskard.core.suite import Suite
from giskard.scanner import Scanner
from giskard.scanner.result import ScanResult
from giskard.client.python_utils import warning


def test_scanner_returns_non_empty_scan_result(german_credit_data, german_credit_model):
    scanner = Scanner()
    result = scanner.analyze(german_credit_model, german_credit_data)

    assert isinstance(result, ScanResult)
    assert result.has_issues()

    test_suite = result.generate_test_suite()
    assert isinstance(test_suite, Suite)


def test_scanner_should_work_with_empty_model_feature_names(german_credit_data, german_credit_model):
    scanner = Scanner()
    german_credit_model.meta.feature_names = None
    result = scanner.analyze(german_credit_model, german_credit_data)

    assert isinstance(result, ScanResult)
    assert result.has_issues()


def test_scanner_raises_exception_if_no_detectors_available(german_credit_data, german_credit_model):
    scanner = Scanner(only="non-existent-detector")

    with pytest.raises(RuntimeError):
        scanner.analyze(german_credit_model, german_credit_data)


def test_warning_duplicate_index(german_credit_model, german_credit_data):
    df = german_credit_data.df.copy()
    new_row = df.loc[1]
    df = df.append(new_row)

    dataset = Dataset(
        df=df,
        target=german_credit_data.target,
        cat_columns=german_credit_data.cat_columns
    )

    scanner = Scanner()

    with pytest.warns(match="You dataframe has duplicate indexes, which is currently not supported. "
                            "We have to reset the dataframe index to avoid issues."):
        scanner.analyze(german_credit_model, dataset)
