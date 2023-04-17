import pytest

import giskard.ml_worker.testing.tests.metamorphic as metamorphic
from giskard.datasets.base import Dataset


def _test_metamorphic_increasing_regression(ds: Dataset, model, threshold):
    perturbation = {"bmi": lambda x: x.bmi + x.bmi * 0.1}
    results = metamorphic.test_metamorphic_increasing(dataset=ds, model=model, perturbation_dict=perturbation,
                                                      threshold=threshold)

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.44
    return results.passed


def _test_metamorphic_decreasing_regression(ds: Dataset, model, threshold):
    perturbation = {"age": lambda x: x.age - x.age * 0.1}
    results = metamorphic.test_metamorphic_decreasing(dataset=ds, model=model, perturbation_dict=perturbation,
                                                      threshold=threshold)
    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.54
    return results.passed


def _test_metamorphic_increasing_classification(df, model, threshold):
    perturbation = {"duration_in_month": lambda x: x.duration_in_month + x.duration_in_month * 0.5}
    results = metamorphic.test_metamorphic_increasing(dataset=df, model=model, perturbation_dict=perturbation,
                                                      threshold=threshold,
                                                      classification_label=model.meta.classification_labels[0])

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def _test_metamorphic_decreasing_classification(df, model, threshold):
    perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
    results = metamorphic.test_metamorphic_decreasing(dataset=df, model=model, perturbation_dict=perturbation,
                                                      threshold=threshold,
                                                      classification_label=model.meta.classification_labels[0])

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model, 0.8)


def test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model, 0.8)


def test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.3)
    assert not _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)


def test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)
    assert not _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.6)


def test_metamorphic_decreasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):
        perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
        metamorphic.test_metamorphic_decreasing(dataset=german_credit_test_data, model=german_credit_model,
                                                perturbation_dict=perturbation, threshold=0.5,
                                                classification_label="random_value")


def test_metamorphic_increasing_exception(german_credit_test_data, german_credit_model):
    with pytest.raises(Exception):
        perturbation = {"duration_in_month": lambda x: x.duration_in_month * 0.5}
        metamorphic.test_metamorphic_increasing(dataset=german_credit_test_data, model=german_credit_model,
                                                perturbation_dict=perturbation, threshold=0.5,
                                                classification_label="random_value")


def test_metamorphic_increasing_t_test(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}

    results = metamorphic.test_metamorphic_increasing_t_test(dataset=german_credit_test_data, model=german_credit_model,
                                                             perturbation_dict=perturbation, critical_quantile=0.05,
                                                             classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_t_test(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}

    results = metamorphic.test_metamorphic_decreasing_t_test(dataset=german_credit_test_data, model=german_credit_model,
                                                             perturbation_dict=perturbation, critical_quantile=0.05,
                                                             classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_wilcoxon(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}

    results = metamorphic.test_metamorphic_increasing_wilcoxon(dataset=german_credit_test_data,
                                                               model=german_credit_model,
                                                               perturbation_dict=perturbation, critical_quantile=0.05,
                                                               classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_wilcoxon(german_credit_test_data, german_credit_model):
    perturbation = {"sex": lambda x: "female" if x.sex == "male" else "male"}

    results = metamorphic.test_metamorphic_decreasing_wilcoxon(dataset=german_credit_test_data,
                                                               model=german_credit_model,
                                                               perturbation_dict=perturbation, critical_quantile=0.05,
                                                               classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_t_test_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}

    results = metamorphic.test_metamorphic_increasing_t_test(dataset=german_credit_test_data, model=german_credit_model,
                                                             perturbation_dict=perturbation, critical_quantile=0.05,
                                                             classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_t_test_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}

    results = metamorphic.test_metamorphic_decreasing_t_test(dataset=german_credit_test_data, model=german_credit_model,
                                                             perturbation_dict=perturbation, critical_quantile=0.05,
                                                             classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_increasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}

    results = metamorphic.test_metamorphic_increasing_wilcoxon(dataset=german_credit_test_data,
                                                               model=german_credit_model,
                                                               perturbation_dict=perturbation, critical_quantile=0.05,
                                                               classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"


def test_metamorphic_decreasing_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    perturbation = {}

    results = metamorphic.test_metamorphic_decreasing_wilcoxon(dataset=german_credit_test_data,
                                                               model=german_credit_model,
                                                               perturbation_dict=perturbation, critical_quantile=0.05,
                                                               classification_label="Default")
    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert not results.passed, f"metric = {results.metric}"
