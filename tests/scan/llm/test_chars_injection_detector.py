from unittest.mock import Mock, patch

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.scanner.llm.llm_chars_injection_detector import LLMCharsInjectionDetector
from giskard.testing.tests.llm.injections import CharInjectionResult


@patch("giskard.scanner.llm.llm_chars_injection_detector.LLMCharInjector")
def test_chars_injection_detector_flow(LLMCharInjector):
    model = Mock()
    model.meta.name = "Test Model"
    model.meta.description = "Test Description"

    dataset = Dataset(pd.DataFrame({"feat": ["input 1"]}))

    injector = Mock()
    LLMCharInjector.return_value = injector

    injector.run.side_effect = [
        # First run
        [
            CharInjectionResult(
                char="a",
                feature="feat",
                fail_rate=0.1,
                vulnerable=False,
                vulnerable_mask=[False],
                original_dataset=Mock(),
                perturbed_dataset=Mock(),
                predictions=Mock(),
                original_predictions=Mock(),
            )
        ],
        # Second run
        [
            CharInjectionResult(
                char="a",
                feature="feat",
                fail_rate=0.1,
                vulnerable=True,
                vulnerable_mask=[True],
                original_dataset=Mock(),
                perturbed_dataset=Mock(),
                predictions=Mock(),
                original_predictions=Mock(),
            ),
            CharInjectionResult(
                char="a",
                feature="feat",
                fail_rate=0.1,
                vulnerable=False,
                vulnerable_mask=[False],
                original_dataset=Mock(),
                perturbed_dataset=Mock(),
                predictions=Mock(),
                original_predictions=Mock(),
            ),
            CharInjectionResult(
                char="b",
                feature="feat",
                fail_rate=0.2,
                vulnerable=True,
                vulnerable_mask=[True],
                original_dataset=Mock(),
                perturbed_dataset=Mock(),
                predictions=Mock(),
                original_predictions=Mock(),
            ),
        ],
    ]

    detector = LLMCharsInjectionDetector(
        control_chars=["a", "b"], num_repetitions=13, num_samples=13892, threshold=0.12, output_sensitivity=0.1111
    )

    # First run
    issues = detector.run(model, dataset)

    assert len(issues) == 0
    LLMCharInjector.assert_called_once_with(
        chars=["a", "b"], max_repetitions=13, threshold=0.12, output_sensitivity=0.1111
    )

    # Second run
    issues = detector.run(model, dataset)
    assert len(issues) == 2
    assert issues[0].generate_tests()[0]


def test_chars_injection_detector_skips_if_empty_dataset():
    model = Mock()
    model.meta.name = "Test Model"
    model.meta.description = "Test Description"

    dataset = Dataset(pd.DataFrame({"feat": []}))
    detector = LLMCharsInjectionDetector()
    assert detector.run(model, dataset) == []
