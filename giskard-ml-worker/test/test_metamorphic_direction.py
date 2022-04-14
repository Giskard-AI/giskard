from ml_worker.testing.functions import GiskardTestFunctions


def _test_metamorphic_increasing(german_credit_test_data, german_credit_model, failed_threshold):
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_increasing(
        german_credit_test_data, 'credit_amount', german_credit_model,
        0.5, 0, failed_threshold)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000
    return results.passed


def test_metamorphic_increasing_fail(german_credit_test_data, german_credit_model):
    _test_metamorphic_increasing(german_credit_test_data, german_credit_model, 0.5)


def test_metamorphic_increasing_pass(german_credit_test_data, german_credit_model):
    _test_metamorphic_increasing(german_credit_test_data, german_credit_model, 1)


def _test_metamorphic_decreasing(german_credit_test_data, german_credit_model, failed_threshold):
    tests = GiskardTestFunctions()
    results = tests.test_metamorphic_decreasing(
        german_credit_test_data, 'credit_amount', german_credit_model,
        -0.5, 0, failed_threshold)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000
    return results.passed


def test_metamorphic_decreasing_pass(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_decreasing(german_credit_test_data, german_credit_model, 1)


def test_metamorphic_decreasing_fail(german_credit_test_data, german_credit_model):
    assert not _test_metamorphic_decreasing(german_credit_test_data, german_credit_model, 0.5)
