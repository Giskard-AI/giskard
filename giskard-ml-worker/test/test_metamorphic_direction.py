from ml_worker.testing.functions import GiskardTestFunctions


def _test_metamorphic_increasing_regression(df, model, threshold):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing(
        df=df.copy(),
        column_name='s1',
        model=model,
        perturbation_percent=0.1,
        threshold=threshold
    )

    assert results.element_count == 442
    assert results.missing_count == 0
    assert results.unexpected_count == 202
    return results.passed


def _test_metamorphic_decreasing_regression(df, model, threshold):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=df.copy(),
        column_name='s1',
        model=model,
        perturbation_percent=-0.99,
        threshold=threshold
    )
    assert results.element_count == 442
    assert results.missing_count == 0
    assert results.unexpected_count == 202
    return results.passed


def _test_metamorphic_increasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_increasing(
        df=df.copy(),
        column_name='credit_amount',
        model=model,
        perturbation_percent=0.1,
        threshold=threshold
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 759
    return results.passed


def _test_metamorphic_decreasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=df.copy(),
        column_name='credit_amount',
        model=model,
        perturbation_percent=-0.1,
        threshold=threshold
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 774
    return results.passed


def test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model, 0.8)
    assert not _test_metamorphic_increasing_classification(german_credit_test_data, german_credit_model, 0.7)


def test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model, 0.8)
    assert not _test_metamorphic_decreasing_classification(german_credit_test_data, german_credit_model, 0.7)


def test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)
    assert not _test_metamorphic_increasing_regression(diabetes_dataset, linear_regression_diabetes, 0.3)


def test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes):
    assert _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.5)
    assert not _test_metamorphic_decreasing_regression(diabetes_dataset, linear_regression_diabetes, 0.4)


def test_regression_increasing(linear_regression_diabetes, diabetes_dataset):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=diabetes_dataset,
        column_name='age',
        model=linear_regression_diabetes,
        perturbation_percent=0.5,
        threshold=0.6)

    assert results.element_count == len(diabetes_dataset)
    assert results.missing_count == 0
    assert results.unexpected_count == 240
    return results.passed


def test_regression_decreasing(linear_regression_diabetes, diabetes_dataset):
    tests = GiskardTestFunctions()
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=diabetes_dataset,
        column_name='age',
        model=linear_regression_diabetes,
        perturbation_percent=-0.5,
        threshold=0.6)

    assert results.element_count == len(diabetes_dataset)
    assert results.missing_count == 0
    assert results.unexpected_count == 202
    return results.passed
