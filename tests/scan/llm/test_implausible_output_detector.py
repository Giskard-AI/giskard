from unittest.mock import Mock, patch, sentinel

import pandas as pd

from giskard import Dataset
from giskard.core.test_result import TestResultStatus
from giskard.llm.evaluators.base import EvaluationResult, EvaluationResultExample
from giskard.scanner.llm.llm_implausible_output_detector import LLMImplausibleOutputDetector


@patch("giskard.scanner.llm.llm_implausible_output_detector.ImplausibleDataGenerator")
@patch("giskard.scanner.llm.llm_implausible_output_detector.PlausibilityEvaluator")
def test_implausible_output_detector_flow(PlausibilityEvaluator, ImplausibleDataGenerator):
    model = Mock()
    model.meta.name = "Test Model"
    model.meta.description = "Test Description"

    dataset = Mock(column_types=sentinel.coltypes)

    generator = Mock()
    evaluator = Mock()
    ImplausibleDataGenerator.return_value = generator
    PlausibilityEvaluator.return_value = evaluator

    eval_dataset = Dataset(pd.DataFrame({"feat": ["input 1", "input 2", "input 3"]}))
    generator.generate_dataset.return_value = eval_dataset
    evaluator.evaluate.side_effect = [
        EvaluationResult(results=[EvaluationResultExample(sample={"sample": 1}, status=TestResultStatus.PASSED)]),
        EvaluationResult(results=[EvaluationResultExample(sample={"sample": 1}, status=TestResultStatus.FAILED)]),
    ]

    detector = LLMImplausibleOutputDetector(num_samples=13892)
    issues = detector.run(model, dataset)

    assert len(issues) == 0
    generator.generate_dataset.assert_called_once_with(model, num_samples=13892, column_types=sentinel.coltypes)
    evaluator.evaluate.assert_called_once_with(model, eval_dataset)

    issues = detector.run(model, dataset)
    assert len(issues) == 1
    assert issues[0].generate_tests()[0]
    assert issues[0].dataset == eval_dataset

    # Issues must contain the "metric" name
    assert "metric" in issues[0].meta
    assert "metric_value" in issues[0].meta
