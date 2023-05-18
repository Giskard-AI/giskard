from giskard.scanner.robustness.text_perturbation_detector import TextPerturbationDetector


def test_perturbation_classification(enron_model, enron_data):
    # @TODO: add feature-specific tests
    analyzer = TextPerturbationDetector(threshold=0.01)
    res = analyzer.run(enron_model, enron_data)
    assert res
