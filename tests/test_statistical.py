import pytest

import giskard.testing.tests.statistic as statistical
from giskard.registry.slicing_function import SlicingFunction


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.1, 0.20, 500),
        ("german_credit_data", "german_credit_model", 1, 0.5, 0.80, 500),
        ("enron_data", "enron_model", 0, 0.1, 0.32, 25),
    ],
)
def test_statistical(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = statistical.test_right_label(
        model=model,
        dataset=data.slice(SlicingFunction(lambda df: df.head(len(df) // 2), row_level=False)),
        classification_label=model.classification_labels[label],
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.3, 0.40, 10),
        ("german_credit_data", "german_credit_model", 1, 0.5, 0.60, 10),
        ("enron_data", "enron_model", 0, 0.01, 0.1, 10),
    ],
)
def test_statistical_filtered(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = statistical.test_right_label(
        model=model,
        dataset=data.slice(SlicingFunction(lambda df: df.head(10), row_level=False)),
        classification_label=model.classification_labels[label],
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.1, 0.34, 500),
        ("german_credit_data", "german_credit_model", 1, 0.1, 0.34, 500),
        ("enron_data", "enron_model", 0, 0.1, 0.32, 25),
    ],
)
def test_output_in_range_model(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = statistical.test_output_in_range(
        model=model,
        dataset=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        classification_label=model.classification_labels[label],
        min_range=0.3,
        max_range=0.7,
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.1, 0.28, 221)],
)
def test_output_in_range_reg(data, model, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    results = statistical.test_output_in_range(
        model=request.getfixturevalue(model),
        dataset=data.slice(SlicingFunction(lambda df: df.head(len(df) // 2), row_level=False)),
        min_range=100,
        max_range=150,
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model",
    [("german_credit_data", "german_credit_model")],
)
def test_disparate_impact(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = statistical.test_disparate_impact(
        model=model,
        dataset=data,
        protected_slicing_function=SlicingFunction(lambda df: df[df.sex == "female"], row_level=False),
        unprotected_slicing_function=SlicingFunction(lambda df: df[df.sex == "male"], row_level=False),
        positive_outcome="Not default",
    ).execute()
    assert results.passed, f"DI = {results.metric}"


@pytest.mark.parametrize(
    "data,model",
    [("titanic_dataset", "titanic_model")],
)
def test_nominal_association(data, model, request):
    import pandas as pd

    import giskard

    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    @giskard.slicing_function
    def sff(row: pd.Series):
        return row.Sex == "female"

    @giskard.slicing_function
    def sfm(row: pd.Series):
        return row.Sex == "male"

    results_theil_u_f = statistical.test_nominal_association(model=model, dataset=data, slicing_function=sff).execute()

    assert results_theil_u_f.metric == pytest.approx(0.7, abs=1e-2)
    assert not results_theil_u_f.passed

    results_theil_u_f_bench = statistical.test_theil_u(model=model, dataset=data, slicing_function=sff).execute()
    assert results_theil_u_f.metric == pytest.approx(results_theil_u_f_bench.metric, abs=1e-2)

    results_theil_u_m = statistical.test_nominal_association(model=model, dataset=data, slicing_function=sfm).execute()
    assert results_theil_u_m.metric == pytest.approx(0.7, abs=1e-2)
    assert not results_theil_u_f.passed

    results_cramer_v_f = statistical.test_nominal_association(
        model=model, dataset=data, slicing_function=sff, method="cramer_v"
    ).execute()

    assert not results_cramer_v_f.passed

    results_cramer_v_m = statistical.test_nominal_association(
        model=model, dataset=data, slicing_function=sfm, method="cramer_v"
    ).execute()
    assert not results_cramer_v_m.passed

    results_mutual_information_f = statistical.test_nominal_association(
        model=model, dataset=data, slicing_function=sff, method="mutual_information"
    ).execute()

    assert not results_mutual_information_f.passed

    results_mutual_information_m = statistical.test_nominal_association(
        model=model, dataset=data, slicing_function=sfm, method="mutual_information"
    ).execute()
    assert not results_mutual_information_m.passed
