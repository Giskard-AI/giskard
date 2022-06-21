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


def test_drift_ks_stat():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_ks(reference_series=SERIES_100_A,
                                     actual_series=SERIES_100_A).metric == 0

    assert pytest.approx(tests.drift.test_drift_ks(
        reference_series=SERIES_100_A,
        actual_series=SERIES_100_B).metric, 0.1) == 1

    assert pytest.approx(tests.drift.test_drift_ks(
        reference_series=SERIES_1,
        actual_series=SERIES_2).metric, 0.1) == 0.3


def test_drift_ks_stat_pass_fail():
    tests = GiskardTestFunctions()
    assert not tests.drift.test_drift_ks(reference_series=SERIES_1,
                                         actual_series=SERIES_2,
                                         threshold=0.05).passed
    # assert tests.drift.test_drift_ks(reference_series=SERIES_1, actual_series=SERIES_2, threshold=0.4).passed


def test_drift_earth_movers_distance():
    tests = GiskardTestFunctions()

    assert tests.drift.test_drift_earth_movers_distance(reference_series=SERIES_100_1,
                                                        actual_series=SERIES_100_1).metric == 0

    assert pytest.approx(tests.drift.test_drift_earth_movers_distance(
        reference_series=SERIES_100_1,
        actual_series=SERIES_100_2).metric, 0.1) == 1

    assert pytest.approx(tests.drift.test_drift_earth_movers_distance(
        reference_series=SERIES_1_NUM,
        actual_series=SERIES_2_NUM).metric, 0.1) == 0.3


def test_drift_earth_movers_distance_pass_fail():
    tests = GiskardTestFunctions()
    assert not tests.drift.test_drift_earth_movers_distance(reference_series=SERIES_1_NUM,
                                                            actual_series=SERIES_2_NUM,
                                                            threshold=0.2).passed

    assert tests.drift.test_drift_earth_movers_distance(reference_series=SERIES_1_NUM,
                                                        actual_series=SERIES_2_NUM,
                                                        threshold=0.4).passed


def _test_drift_data_psi(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_psi(
        reference_ds=german_credit_test_data.df[:len(german_credit_test_data.df) // 2],
        actual_ds=german_credit_test_data.df[len(german_credit_test_data.df) // 2:],
        column_name='personal_status',
        threshold=threshold)

    assert round(results.metric, 2) == 0.00
    return results.passed


def test_drift_data_psi_pass_fail(german_credit_test_data):
    assert not _test_drift_data_psi(german_credit_test_data, 0)
    assert _test_drift_data_psi(german_credit_test_data, 0.1)


def _test_drift_data_psi_max_categories(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_psi(
        reference_ds=german_credit_test_data.df[:len(german_credit_test_data.df) // 2],
        actual_ds=german_credit_test_data.df[len(german_credit_test_data.df) // 2:],
        column_name='personal_status',
        max_categories=2,
        threshold=threshold)

    assert round(results.metric, 2) == 0.00
    return results.passed


def test_drift_data_psi_max_categories_pass_fail(german_credit_test_data):
    assert not _test_drift_data_psi_max_categories(german_credit_test_data, 0)
    assert _test_drift_data_psi_max_categories(german_credit_test_data, 0.1)


def _test_drift_data_chi_square(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_chi_square(
        reference_ds=german_credit_test_data.df[:len(german_credit_test_data.df) // 2],
        actual_ds=german_credit_test_data.df[len(german_credit_test_data.df) // 2:],
        column_name='personal_status',
        threshold=threshold)

    assert round(results.metric, 2) == 0.76
    return results.passed


def test_drift_data_chi_squared_pass_fail(german_credit_test_data):
    assert not _test_drift_data_chi_square(german_credit_test_data, 0.8)
    assert _test_drift_data_chi_square(german_credit_test_data, 0.1)


def _test_drift_data_chi_square_max_categories(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_chi_square(
        reference_ds=german_credit_test_data.df[:len(german_credit_test_data.df) // 2],
        actual_ds=german_credit_test_data.df[len(german_credit_test_data.df) // 2:],
        column_name='personal_status',
        max_categories=2,
        threshold=threshold)

    assert round(results.metric, 2) == 0.76
    return results.passed


def test_drift_data_chi_square_max_categories_pass_fail(german_credit_test_data):
    assert not _test_drift_data_chi_square_max_categories(german_credit_test_data, 0.8)
    assert _test_drift_data_chi_square_max_categories(german_credit_test_data, 0.1)


def _test_drift_prediction_psi(german_credit_test_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_prediction_psi(
        reference_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.022
    return results.passed


def test_drift_prediction_psi_pass_fail(german_credit_test_data, german_credit_model):
    assert not _test_drift_prediction_psi(german_credit_test_data, german_credit_model, 0.02)
    assert _test_drift_prediction_psi(german_credit_test_data, german_credit_model, 0.1)


def _test_drift_prediction_chi_square(german_credit_test_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_prediction_chi_square(
        reference_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        threshold=threshold)

    assert round(results.metric, 2) == 0
    return results.passed


def test_drift_prediction_chi_square_pass_fail(german_credit_test_data, german_credit_model):
    assert not _test_drift_prediction_chi_square(german_credit_test_data, german_credit_model, 9)


def _test_drift_reg_output_ks(diabetes_dataset_with_target, linear_regression_diabetes, threshold=0.02):
    tests = GiskardTestFunctions()
    ds = diabetes_dataset_with_target
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
        model=linear_regression_diabetes,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.6899029016494751
    return results.passed


def test_drift_reg_output_ks_pass_fail(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_drift_reg_output_ks(diabetes_dataset_with_target, linear_regression_diabetes, 0.05)


def _test_drift_clf_prob_ks(german_credit_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    ds = german_credit_data
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        threshold=threshold,
        classification_label='Default')

    assert pytest.approx(results.metric, 0.1) == 0.14973188936710358
    return results.passed


def test_drift_clf_prob_ks_pass_fail(german_credit_data, german_credit_model):
    assert not _test_drift_clf_prob_ks(german_credit_data, german_credit_model, 0.2)
    assert _test_drift_clf_prob_ks(german_credit_data, german_credit_model, 0.05)


def _test_drift_reg_output_earth_movers_distance(diabetes_dataset_with_target, linear_regression_diabetes,
                                                 threshold=0.02):
    tests = GiskardTestFunctions()
    ds = diabetes_dataset_with_target
    results = tests.drift.test_drift_prediction_earth_movers_distance(
        reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
        model=linear_regression_diabetes,
        threshold=threshold)

    assert pytest.approx(results.metric, 0.1) == 0.02
    return results.passed


def test_drift_reg_output_earth_movers_distance_pass_fail(diabetes_dataset_with_target, linear_regression_diabetes):
    assert not _test_drift_reg_output_earth_movers_distance(
        diabetes_dataset_with_target, linear_regression_diabetes, 0.01)
    assert _test_drift_reg_output_earth_movers_distance(
        diabetes_dataset_with_target, linear_regression_diabetes, 0.03)


def _test_drift_clf_prob_earth_movers_distance(german_credit_data, german_credit_model,
                                               threshold=0.02):
    tests = GiskardTestFunctions()
    ds = german_credit_data
    results = tests.drift.test_drift_prediction_earth_movers_distance(
        reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        classification_label='Default',
        threshold=threshold)

    assert pytest.approx(results.metric, 0.01) == 0.034422677010297775
    return results.passed


def test_drift_clf_prob_earth_movers_distance_pass_fail(german_credit_data, german_credit_model):
    assert not _test_drift_clf_prob_earth_movers_distance(german_credit_data, german_credit_model, 0.01)
    assert _test_drift_clf_prob_earth_movers_distance(german_credit_data, german_credit_model, 0.04)


def test_drift_clf_prob_ks_exception(german_credit_data, german_credit_model, threshold=0.02):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        ds = german_credit_data
        results = tests.drift.test_drift_prediction_ks(
            reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
            actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
            model=german_credit_model,
            threshold=threshold,
            classification_label='random_value')
