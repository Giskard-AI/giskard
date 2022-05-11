from ml_worker.testing.functions import GiskardTestFunctions


def test_metamorphic_invariance_no_change(german_credit_test_data, german_credit_model):
    perturbation = {}
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == 0
    assert results.missing_count == 0
    assert results.unexpected_count == 0


def _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, threshold):
    perturbation = {
        "sex": lambda x: 'female' if x.sex == 'male' else 'male'
    }
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation,
                                                            threshold=threshold)
    assert results.element_count == len(german_credit_test_data)
    assert results.missing_count == 0
    assert results.unexpected_count == 33
    return results.passed


def test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 0.04)
    assert not _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 0.03)


def test_metamorphic_invariance_2_perturbations(german_credit_test_data, german_credit_model):
    perturbation = {
        "duration_in_month": lambda x: x.duration_in_month * 2,
        "sex": lambda x: 'female' if x.sex == 'male' else 'male'
    }
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == len(german_credit_test_data)
    assert results.missing_count == 0
    assert results.unexpected_count == 142


def test_metamorphic_invariance_some_rows(german_credit_test_data, german_credit_model):
    perturbation = {
        "sex": lambda x: 'female' if x.sex == 'male' else x.sex
    }
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_invariance(german_credit_test_data, german_credit_model, perturbation)
    assert results.element_count == 690
    assert results.missing_count == 0
    assert results.unexpected_count == 24
