import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_drift_data_psi(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_psi(
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
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
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
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
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
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
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
        column_name='personal_status',
        max_categories=2,
        threshold=threshold)

    assert round(results.metric, 2) == 0.76
    return results.passed


def test_drift_data_chi_square_max_categories_pass_fail(german_credit_test_data):
    assert not _test_drift_data_chi_square_max_categories(german_credit_test_data, 0.8)
    assert _test_drift_data_chi_square_max_categories(german_credit_test_data, 0.1)


def _test_drift_data_ks(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_ks(
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
        column_name='credit_amount',
        threshold=threshold)

    assert round(results.metric, 2) == 0.72
    return results.passed


def test_drift_data_ks_pass_fail(german_credit_test_data):
    assert not _test_drift_data_ks(german_credit_test_data, 0.9)
    assert _test_drift_data_ks(german_credit_test_data, 0.5)


def _test_drift_data_earth_movers_distance(german_credit_test_data, threshold=0.05):
    tests = GiskardTestFunctions()
    results = tests.drift.test_drift_earth_movers_distance(
        reference_ds=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=german_credit_test_data.slice(lambda df: df.tail(len(df) // 2)),
        column_name='credit_amount',
        threshold=threshold)

    assert round(results.metric, 2) == 0.01
    return results.passed


def test_drift_data_earth_movers_distance_pass_fail(german_credit_test_data):
    assert not _test_drift_data_earth_movers_distance(german_credit_test_data, 0.00001)
    assert _test_drift_data_earth_movers_distance(german_credit_test_data, 0.5)


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
    assert not _test_drift_reg_output_ks(diabetes_dataset_with_target, linear_regression_diabetes, 0.7)
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


def _test_drift_clf_prob_ks_small_dataset(german_credit_data, german_credit_model, threshold=0.02):
    tests = GiskardTestFunctions()
    ds = german_credit_data
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=ds.slice(lambda df: df.head(9)),
        actual_slice=ds.slice(lambda df: df.tail(10)),
        model=german_credit_model,
        threshold=threshold,
        classification_label='Default')

    assert pytest.approx(results.metric, 0.1) == 0.90
    return results.passed


def test_drift_clf_prob_ks_pass_fail_small_dataset(german_credit_data, german_credit_model):
    assert not _test_drift_clf_prob_ks_small_dataset(german_credit_data, german_credit_model, 1)
    assert _test_drift_clf_prob_ks_small_dataset(german_credit_data, german_credit_model, 0.05)


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
