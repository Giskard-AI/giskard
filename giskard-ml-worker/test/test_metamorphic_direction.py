import pytest

from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.testing.functions import GiskardTestFunctions


def _test_metamorphic_increasing_regression(ds: GiskardDataset, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {
        "bmi": lambda x: x.bmi + x.bmi * 0.1}
    results = tests.metamorphic.test_metamorphic_increasing(
        df=ds,
        model=model,
        perturbation_dict=perturbation,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.44
    return results.passed


def _test_metamorphic_decreasing_regression(ds: GiskardDataset, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {
        "age": lambda x: x.age - x.age * 0.1}
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=ds,
        model=model,
        perturbation_dict=perturbation,
        threshold=threshold
    )
    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 0.54
    return results.passed


def _test_metamorphic_increasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {
        "duration_in_month": lambda x: x.duration_in_month + x.duration_in_month * 0.5}
    results = tests.metamorphic.test_metamorphic_increasing(
        df=df,
        model=model,
        classification_label=model.classification_labels[0],
        perturbation_dict=perturbation,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000
    assert results.metric == 1
    return results.passed


def _test_metamorphic_decreasing_classification(df, model, threshold):
    tests = GiskardTestFunctions()
    perturbation = {
        "duration_in_month": lambda x: x.duration_in_month - x.duration_in_month * 0.5}
    results = tests.metamorphic.test_metamorphic_decreasing(
        df=df,
        model=model,
        classification_label=model.classification_labels[0],
        perturbation_dict=perturbation,
        threshold=threshold
    )

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
        tests = GiskardTestFunctions()
        perturbation = {
            "duration_in_month": lambda x: x.duration_in_month - x.duration_in_month * 0.5}
        results = tests.metamorphic.test_metamorphic_decreasing(
            df=german_credit_test_data,
            model=german_credit_model,
            classification_label='random_value',
            perturbation_dict=perturbation,
            threshold=0.5
        )


def test_metamorphic_increasing_enron(enron_data, enron_model):
    import nlpaug.augmenter.word as naw  # uncomment for text perturbation
    aug = naw.SpellingAug(dict_path=None, name='Spelling_Aug', aug_min=1, aug_max=10, aug_p=0.3, stopwords=None,
                          tokenizer=None, reverse_tokenizer=None, include_reverse=True, stopwords_regex=None, verbose=0) # uncomment for text perturbation
    tests = GiskardTestFunctions()
    perturbation = {
        "Content": lambda x: aug.augment(x["Content"])}
    results = tests.metamorphic.test_metamorphic_increasing(
        df=enron_data,
        model=enron_model,
        classification_label='INFLUENCE',
        perturbation_dict=perturbation,
        threshold=0.5
    )
