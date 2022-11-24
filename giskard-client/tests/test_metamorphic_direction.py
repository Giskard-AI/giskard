import pytest

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.testing.functions import GiskardTestFunctions


def _test_metamorphic_increasing_regression(ds: GiskardDataset, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {"bmi": lambda x: x.bmi + x.bmi * 0.1}
    results = tests.metamorphic.test_metamorphic_increasing(
        df=ds, model=model, perturbation_dict=perturbation, threshold=threshold
    )

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.44
    return results.passed


def _test_metamorphic_decreasing_regression(ds: GiskardDataset, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {"age": lambda x: x.age - x.age * 0.1}
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=ds, model=model, perturbation_dict=perturbation, threshold=threshold
    )
    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.54
    return results.passed


def _test_metamorphic_increasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {"duration_in_month": lambda x: x.duration_in_month + x.duration_in_month * 0.5}
    results = tests.metamorphic.test_metamorphic_increasing(
        df=df,
        model=model,
        classification_label=model.classification_labels[0],
        perturbation_dict=perturbation,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def _test_metamorphic_decreasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=df,
        model=model,
        classification_label=model.classification_labels[0],
        perturbation_dict=perturbation,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_increasing_classification(
        german_credit_test_data, german_credit_model, 0.8
    )


def test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_decreasing_classification(
        german_credit_test_data, german_credit_model, 0.8
    )


def test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_increasing_regression(
        diabetes_dataset, linear_regression_diabetes, 0.3
    )
    assert not _test_metamorphic_increasing_regression(
        diabetes_dataset, linear_regression_diabetes, 0.5
    )


def test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_decreasing_regression(
        diabetes_dataset, linear_regression_diabetes, 0.5
    )
    assert not _test_metamorphic_decreasing_regression(
        diabetes_dataset, linear_regression_diabetes, 0.6
    )


def test_metamorphic_decreasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
        tests.metamorphic.test_metamorphic_decreasing(
            df=german_credit_test_data,
            model=german_credit_model,
            classification_label="random_value",
            perturbation_dict=perturbation,
            threshold=0.5,
        )


def test_metamorphic_increasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):
        tests = GiskardTestFunctions()
        perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
        tests.metamorphic.test_metamorphic_increasing(
            df=german_credit_test_data,
            model=german_credit_model,
            classification_label="random_value",
            perturbation_dict=perturbation,
            threshold=0.5,
        )

def test_metamorphic_increasing_t_test(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing_t_test(df=german_credit_test_data,
                                                                   model=german_credit_model,
                                                                   perturbation_dict=perturbation,
                                                                   critical_quantile=0.05,
                                                                   classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"

def test_metamorphic_decreasing_t_test(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing_t_test(df=german_credit_test_data,
                                                                   model=german_credit_model,
                                                                   perturbation_dict=perturbation,
                                                                   critical_quantile=0.05,
                                                                   classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"

def test_metamorphic_increasing_wilcoxon(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing_wilcoxon(df=german_credit_test_data,
                                                                     model=german_credit_model,
                                                                     perturbation_dict=perturbation,
                                                                     critical_quantile=0.05,
                                                                     classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"

def test_metamorphic_decreasing_wilcoxon(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing_wilcoxon(df=german_credit_test_data,
                                                                     model=german_credit_model,
                                                                     perturbation_dict=perturbation,
                                                                     critical_quantile=0.05,
                                                                     classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"

def test_metamorphic_increasing_t_test_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing_t_test(df=german_credit_test_data,
                                                                   model=german_credit_model,
                                                                   perturbation_dict=perturbation,
                                                                   critical_quantile=0.05,
                                                                   classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"

def test_metamorphic_decreasing_t_test_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing_t_test(df=german_credit_test_data,
                                                                   model=german_credit_model,
                                                                   perturbation_dict=perturbation,
                                                                   critical_quantile=0.05,
                                                                   classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"

def test_metamorphic_increasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing_wilcoxon(df=german_credit_test_data,
                                                                     model=german_credit_model,
                                                                     perturbation_dict=perturbation,
                                                                     critical_quantile=0.05,
                                                                     classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"

def test_metamorphic_decreasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing_wilcoxon(df=german_credit_test_data,
                                                                     model=german_credit_model,
                                                                     perturbation_dict=perturbation,
                                                                     critical_quantile=0.05,
                                                                     classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"