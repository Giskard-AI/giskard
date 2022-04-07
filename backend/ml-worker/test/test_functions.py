import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def test_metamorphic_invariance_no_change(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == 0
    assert results.missing_count == 0
    assert results.unexpected_count == 0


def test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model):
    perturbation = {
        "sex": lambda x: 'female' if x.sex == 'male' else 'male'
    }
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == len(german_credit_test_data)
    assert results.missing_count == 0
    assert results.unexpected_count == 64


def test_metamorphic_invariance_2_perturbations(german_credit_test_data, german_credit_model):
    perturbation = {
        "duration_in_month": lambda x: x.duration_in_month * 2,
        "sex": lambda x: 'female' if x.sex == 'male' else 'male'
    }
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == len(german_credit_test_data)
    assert results.missing_count == 0
    assert results.unexpected_count == 110


def test_metamorphic_invariance_some_rows(german_credit_test_data, german_credit_model):
    perturbation = {
        "sex": lambda x: 'female' if x.sex == 'male' else x.sex
    }
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == 690
    assert results.missing_count == 0
    assert results.unexpected_count == 41


def test_metamorphic_increasing(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_increasing(
        german_credit_test_data, 'credit_amount', german_credit_model,
        0.5, 0)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000


def test_metamorphic_decreasing(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_decreasing(
        german_credit_test_data, 'credit_amount', german_credit_model,
        -0.5, 0)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000


def test_heuristic(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        1)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 768
    assert results.unexpected_percent == 76.8


def test_heuristic_opposite(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        0)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000 - 768
    assert pytest.approx(results.unexpected_percent, 0.1) == 100 - 76.8


def test_heuristic_proba_limits(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.test_heuristic(german_credit_test_data, german_credit_model, 0, min_proba=0.4, max_proba=0.6)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 914
    assert pytest.approx(results.unexpected_percent, 0.1) == 91.4
