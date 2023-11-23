import numpy as np
import pytest

from giskard import Model
from giskard.scanner.correlation.spurious_correlation_detector import SpuriousCorrelationDetector
from tests.dill_pool import DillProcessPoolExecutor


def _make_titanic_biased_model(minimal=False):
    def biased_classifier(df):
        p = 1.0 * (df.Sex == "male")
        return np.stack([p, 1 - p], axis=1)

    feature_names = ["Sex"] if minimal else None
    model = Model(
        biased_classifier,
        model_type="classification",
        classification_labels=["no", "yes"],
        feature_names=feature_names,
    )
    return model


@pytest.mark.memory_expensive
def test_spurious_correlation_is_detected(titanic_dataset):
    model = _make_titanic_biased_model()

    def _spurious_correlation(model, dataset):
        return SpuriousCorrelationDetector().run(model, dataset)

    with DillProcessPoolExecutor() as executor:
        issues = executor.submit_and_wait(_spurious_correlation, model, titanic_dataset)

        assert len(issues) > 0
        assert '`Sex` == "male"' in [str(i.slicing_fn) for i in issues]

        rng = np.random.default_rng(1943)

        def random_classifier(df):
            p = rng.uniform(size=len(df))
            return np.stack([p, 1 - p], axis=1)

        random_model = Model(
            random_classifier,
            model_type="classification",
            classification_labels=["no", "yes"],
        )
        issues = executor.submit_and_wait(_spurious_correlation, random_model, titanic_dataset)

        assert not issues


@pytest.mark.memory_expensive
def test_threshold(titanic_model, titanic_dataset):
    def _spurious_correlation(model, dataset, threshold):
        return SpuriousCorrelationDetector(threshold=threshold).run(model, dataset)

    with DillProcessPoolExecutor() as executor:
        issues = executor.submit_and_wait(_spurious_correlation, titanic_model, titanic_dataset, 0.6)
        assert len(issues) > 0

        issues = executor.submit_and_wait(_spurious_correlation, titanic_model, titanic_dataset, 0.9)
        assert not issues


@pytest.mark.parametrize(
    "method,expected_name,expected_value",
    [
        ("theil", "Theil", 0.70),
        ("cramer", "Cramer", 0.89),
        ("mutual_information", "Mutual information", 0.70),
    ],
)
@pytest.mark.memory_expensive
def test_can_choose_association_measures(method, expected_name, expected_value, request):
    titanic_dataset = request.getfixturevalue("titanic_dataset")
    titanic_model = request.getfixturevalue("titanic_model")
    biased_model = _make_titanic_biased_model()

    def _spurious_correlation(model, dataset, method):
        return SpuriousCorrelationDetector(method=method).run(model, dataset)

    with DillProcessPoolExecutor() as executor:
        issues = executor.submit_and_wait(_spurious_correlation, biased_model, titanic_dataset, method)
        assert len(issues) > 0
        assert issues[0].meta["metric_value"] == pytest.approx(1)
        assert expected_name in issues[0].meta["metric"]

        issues = executor.submit_and_wait(_spurious_correlation, titanic_model, titanic_dataset, method)
        assert len(issues) > 0
        assert issues[0].meta["metric_value"] == pytest.approx(expected_value, abs=0.01)
        assert expected_name in issues[0].meta["metric"]


def test_raises_error_for_invalid_measure_method(titanic_model, titanic_dataset):
    with pytest.raises(ValueError):
        detector = SpuriousCorrelationDetector(method="this does not exist!")
        detector.run(titanic_model, titanic_dataset)
