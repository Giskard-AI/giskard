import numpy as np
import pytest

from giskard.ml_worker.testing.functions import GiskardTestFunctions


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.0, "personal_status"), ("enron_data", 2, 1.19, "Week_day")],
)
def test_drift_data_psi(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_psi(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name,max_categories",
    [
        ("german_credit_data", 0.05, 0.0, "personal_status", 2),
        ("enron_data", 2, 0.28, "Week_day", 2),
    ],
)
def test_drift_data_psi_max_categories(
        data, threshold, expected_metric, column_name, max_categories, request
):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_psi(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        max_categories=max_categories,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.76, "personal_status"), ("enron_data", 0, 0, "Week_day")],
)
def test_drift_data_chi_square(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_chi_square(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name,max_categories",
    [
        ("german_credit_data", 0.05, 0.76, "personal_status", 2),
        ("enron_data", 0.02, 0.04, "Week_day", 2),
    ],
)
def test_drift_data_chi_square_max_categories(
        data, threshold, expected_metric, column_name, max_categories, request
):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_chi_square(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        max_categories=max_categories,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.72, "credit_amount"), ("enron_data", 0.05, 0.29, "Hour")],
)
def test_drift_data_ks(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_ks(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.72, "credit_amount"), ("enron_data", 0.05, 0.29, "Hour")],
)
def test_drift_data_ks_with_nan(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    data.df.replace({1169: np.nan}, inplace=True)

    results = tests.drift.test_drift_ks(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.0, "duration_in_month")],
)
def test_drift_data_ks_unique_values(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_ks(
        reference_ds=data.slice(lambda df: df[df["duration_in_month"] == 6]),
        actual_ds=data.slice(lambda df: df[df["duration_in_month"].isin([6, 48])]),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert not results.passed


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 1, 0.01, "credit_amount"), ("enron_data", 1, 0.16, "Hour")],
)
def test_drift_data_earth_movers_distance(data, threshold, expected_metric, column_name, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_earth_movers_distance(
        reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
        actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
        column_name=column_name,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [
        ("german_credit_data", "german_credit_model", 1, 0.02),
        ("enron_data", "enron_model", 2, 1.36),
    ],
)
def test_drift_prediction_psi(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = tests.drift.test_drift_prediction_psi(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=model,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("german_credit_data", "german_credit_model", 0, 0), ("enron_data", "enron_model", -1, 0)],
)
def test_drift_prediction_chi_square(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_chi_square(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0, 0.69)],
)
def test_drift_reg_output_ks(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,classification_label",
    [
        ("german_credit_data", "german_credit_model", 0.05, 0.15, "Default"),
        ("enron_data", "enron_model", 0.05, 0.29, "CALIFORNIA CRISIS"),
    ],
)
def test_drift_clf_prob_ks(data, model, threshold, expected_metric, classification_label, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold,
        classification_label=classification_label,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,classification_label,num_rows",
    [
        ("german_credit_data", "german_credit_model", 0.05, 0.73, "Default", 9),
        ("enron_data", "enron_model", 0.05, 0.99, "CALIFORNIA CRISIS", 9),
        ("german_credit_data", "german_credit_model", 0.05, 1, "Default", 1),
        ("german_credit_data", "german_credit_model", 0.05, 0.99, "Default", 10),
        ("german_credit_data", "german_credit_model", 0.05, 0.83, "Default", 11),
    ],
)
def test_drift_clf_prob_ks_small_dataset(
        data, model, threshold, expected_metric, classification_label, num_rows, request
):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=data.slice(lambda df: df.head(num_rows)),
        actual_slice=data.slice(lambda df: df.tail(num_rows)),
        model=request.getfixturevalue(model),
        threshold=threshold,
        classification_label=classification_label,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,classification_label",
    [("german_credit_data", "german_credit_model", 0.05, 0.29, "Default")],
)
@pytest.mark.skip(reason="#585")
def test_drift_clf_prob_ks_small_unique_dataset(
        data, model, threshold, expected_metric, classification_label, request
):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_ks(
        reference_slice=data.slice(lambda df: df[df["housing"] == "own"]),
        actual_slice=data.slice(lambda df: df[df["housing"].isin(["own", "rent"])]),
        model=request.getfixturevalue(model),
        threshold=threshold,
        classification_label=classification_label,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.05, 0.02)],
)
def test_drift_reg_output_earth_movers_distance(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_earth_movers_distance(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,classification_label",
    [
        ("german_credit_data", "german_credit_model", 0.05, 0.03, "Default"),
        ("enron_data", "enron_model", 0.2, 0.12, "CALIFORNIA CRISIS"),
    ],
)
def test_drift_clf_prob_earth_movers_distance(
        data, model, threshold, expected_metric, classification_label, request
):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.drift.test_drift_prediction_earth_movers_distance(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        classification_label=classification_label,
        threshold=threshold,
    )

    assert round(results.metric, 2) == expected_metric
    assert results.passed


def test_drift_clf_prob_ks_exception(german_credit_data, german_credit_model, threshold=0.02):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        ds = german_credit_data
        tests.drift.test_drift_prediction_ks(
            reference_slice=ds.slice(lambda df: df.head(len(df) // 2)),
            actual_slice=ds.slice(lambda df: df.tail(len(df) // 2)),
            model=german_credit_model,
            threshold=threshold,
            classification_label="random_value",
        )


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.76, "credit_amount")],
)
def test_drift_data_chi_square_exception(data, threshold, expected_metric, column_name, request):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        data = request.getfixturevalue(data)
        tests.drift.test_drift_chi_square(
            reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
            actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
            column_name=column_name,
            threshold=threshold,
        )


@pytest.mark.parametrize(
    "data,threshold,expected_metric,column_name",
    [("german_credit_data", 0.05, 0.72, "personal_status")],
)
def test_drift_data_ks_exception(data, threshold, expected_metric, column_name, request):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        data = request.getfixturevalue(data)
        tests.drift.test_drift_ks(
            reference_ds=data.slice(lambda df: df.head(len(df) // 2)),
            actual_ds=data.slice(lambda df: df.tail(len(df) // 2)),
            column_name=column_name,
            threshold=threshold,
        )
