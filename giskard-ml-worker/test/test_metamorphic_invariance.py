from ml_worker.testing.functions import GiskardTestFunctions


def test_metamorphic_invariance_no_change(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == 0
    assert results.missing_count == 0
    assert results.unexpected_count == 0


def _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, failed_threshold):
    perturbation = {
        "sex": lambda x: 'female' if x.sex == 'male' else 'male'
    }
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation,
                                                failed_threshold=failed_threshold)
    assert results.element_count == len(german_credit_test_data)
    assert results.missing_count == 0
    assert results.unexpected_count == 64
    return results.passed


def test_metamorphic_invariance_male_female_pass(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 0.07)


def test_metamorphic_invariance_male_female_fail(german_credit_test_data, german_credit_model):
    assert not _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 0.06)


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