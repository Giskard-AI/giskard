import math

import pandas as pd
import pytest

from ml_worker.testing.functions import GiskardTestFunctions

SERIES_100_A = pd.Series(['a'] * 100)
SERIES_100_1 = pd.Series([1] * 100)
SERIES_100_B = pd.Series(['b'] * 100)
SERIES_100_2 = pd.Series([2] * 100)
SERIES_1 = pd.Series(['a'] * 50 + ['b'] * 30 + ['c'] * 20)
SERIES_1_NUM = pd.Series([1] * 50 + [2] * 30 + [3] * 20)
SERIES_2 = pd.Series(['a'] * 20 + ['b'] * 30 + ['c'] * 50)
SERIES_2_NUM = pd.Series([1] * 20 + [2] * 30 + [3] * 50)
SERIES_3 = pd.Series(['a'] * 20 + ['c'] * 50 + ['d'] * 30)
SERIES_3_NUM = pd.Series([1] * 20 + [3] * 50 + [4] * 30)


def test_drift_psi():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_psi(expected_series=SERIES_100_A, actual_series=SERIES_100_A).metric == 0

    assert pytest.approx(tests.drift.test_drift_psi(
        expected_series=SERIES_100_A, actual_series=SERIES_100_B).metric, 0.1) == 18.4

    assert pytest.approx(tests.drift.test_drift_psi(
        expected_series=SERIES_1, actual_series=SERIES_2).metric, 0.1) == 0.5


def test_drift_psi_pass_fail():
    tests = GiskardTestFunctions()

    assert not tests.drift.test_drift_psi(expected_series=SERIES_1, actual_series=SERIES_2, threshold=0.4).passed
    assert tests.drift.test_drift_psi(expected_series=SERIES_1, actual_series=SERIES_2, threshold=0.6).passed


def test_drift_psi_max_cat():
    tests = GiskardTestFunctions()
    assert pytest.approx(tests.drift.test_drift_psi(
        expected_series=SERIES_1, actual_series=SERIES_3, max_categories=2).metric, 0.1) == 3.5


def test_drift_chi_square():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_chi_square(expected_series=SERIES_100_A, actual_series=SERIES_100_A).metric == 0

    assert pytest.approx(tests.drift.test_drift_chi_square(
        expected_series=SERIES_100_A, actual_series=SERIES_100_B).metric, 0.1) == math.inf

    assert pytest.approx(tests.drift.test_drift_chi_square(
        expected_series=SERIES_1, actual_series=SERIES_2).metric, 0.1) == 63.0


def test_drift_chi_square_max_cat():
    tests = GiskardTestFunctions()

    assert pytest.approx(
        tests.drift.test_drift_chi_square(
            expected_series=SERIES_1, actual_series=SERIES_3, max_categories=2).metric, 0.1) == 228.0


def test_drift_chi_square_pass_fail():
    tests = GiskardTestFunctions()
    assert not tests.drift.test_drift_chi_square(expected_series=SERIES_1, actual_series=SERIES_2, threshold=62).passed
    assert tests.drift.test_drift_chi_square(expected_series=SERIES_1, actual_series=SERIES_2, threshold=64).passed


def test_drift_ks_stat():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_ks(expected_series=SERIES_100_A, actual_series=SERIES_100_A).metric == 0

    assert pytest.approx(tests.drift.test_drift_ks(
        expected_series=SERIES_100_A, actual_series=SERIES_100_B).metric, 0.1) == 1

    assert pytest.approx(tests.drift.test_drift_ks(
        expected_series=SERIES_1, actual_series=SERIES_2).metric, 0.1) == 0.3


def test_drift_ks_stat_pass_fail():
    tests = GiskardTestFunctions()
    assert not tests.drift.test_drift_ks(expected_series=SERIES_1, actual_series=SERIES_2, threshold=0.2).passed
    assert tests.drift.test_drift_ks(expected_series=SERIES_1, actual_series=SERIES_2, threshold=0.4).passed


def test_drift_earth_movers_distance():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_earth_movers_distance(expected_series=SERIES_100_1,
                                                        actual_series=SERIES_100_1).metric == 0

    assert pytest.approx(tests.drift.test_drift_earth_movers_distance(
        expected_series=SERIES_100_1, actual_series=SERIES_100_2).metric, 0.1) == 1

    assert pytest.approx(tests.drift.test_drift_earth_movers_distance(
        expected_series=SERIES_1_NUM, actual_series=SERIES_2_NUM).metric, 0.1) == 0.3


def test_drift_earth_movers_distance_pass_fail():
    tests = GiskardTestFunctions()
    assert not tests.drift.test_drift_earth_movers_distance(expected_series=SERIES_1_NUM, actual_series=SERIES_2_NUM,
                                                            threshold=0.2).passed
    assert tests.drift.test_drift_earth_movers_distance(expected_series=SERIES_1_NUM, actual_series=SERIES_2_NUM,
                                                        threshold=0.4).passed


def _test_drift_prediction_psi(german_credit_test_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_prediction_psi(
        german_credit_test_data[:len(german_credit_test_data) // 2],
        german_credit_test_data[len(german_credit_test_data) // 2:],
        german_credit_model,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.036
    return results.passed


def test_drift_prediction_psi_pass_fail(german_credit_test_data, german_credit_model):
    assert not _test_drift_prediction_psi(german_credit_test_data, german_credit_model, 0.02)
    assert _test_drift_prediction_psi(german_credit_test_data, german_credit_model, 0.1)


def _test_drift_prediction_chi_square(german_credit_test_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_prediction_chi_square(
        german_credit_test_data[:len(german_credit_test_data) // 2],
        german_credit_test_data[len(german_credit_test_data) // 2:],
        german_credit_model,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 16.2
    return results.passed


def test_drift_prediction_chi_square_pass_fail(german_credit_test_data, german_credit_model):
    assert not _test_drift_prediction_chi_square(german_credit_test_data, german_credit_model, 15)
    assert _test_drift_prediction_chi_square(german_credit_test_data, german_credit_model, 17)


def _test_drift_prediction_ks(diabetes_dataset_with_target, linear_regression_diabetes, threshold=0.02):
    tests = GiskardTestFunctions()
    df = diabetes_dataset_with_target
    results = tests.drift.test_drift_prediction_ks(
        df[:len(df) // 2],
        df[len(df) // 2:],
        linear_regression_diabetes,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.07
    return results.passed


def test_drift_prediction_ks_pass_fail(diabetes_dataset_with_target, linear_regression_diabetes):
    assert not _test_drift_prediction_ks(diabetes_dataset_with_target, linear_regression_diabetes, 0.06)
    assert _test_drift_prediction_ks(diabetes_dataset_with_target, linear_regression_diabetes, 0.08)


def _test_drift_prediction_earth_movers_distance(diabetes_dataset_with_target, linear_regression_diabetes,
                                                 threshold=0.02):
    tests = GiskardTestFunctions()
    df = diabetes_dataset_with_target
    results = tests.drift.test_drift_prediction_earth_movers_distance(
        df[:len(df) // 2],
        df[len(df) // 2:],
        linear_regression_diabetes,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.02
    return results.passed


def test_drift_prediction_earth_movers_distance_pass_fail(diabetes_dataset_with_target, linear_regression_diabetes):
    assert not _test_drift_prediction_earth_movers_distance(
        diabetes_dataset_with_target, linear_regression_diabetes, 0.01)
    assert _test_drift_prediction_earth_movers_distance(
        diabetes_dataset_with_target, linear_regression_diabetes, 0.03)
