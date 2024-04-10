from unittest.mock import Mock, patch, sentinel

import pandas as pd

from giskard import Dataset
from giskard.core.test_result import TestResultStatus
from giskard.llm.evaluators.base import EvaluationResult, EvaluationResultExample
from giskard.scanner.llm.llm_basic_sycophancy_detector import LLMBasicSycophancyDetector


@patch("giskard.scanner.llm.llm_basic_sycophancy_detector.SycophancyDataGenerator")
@patch("giskard.scanner.llm.llm_basic_sycophancy_detector.CoherencyEvaluator")
def test_sycophancy_detector_flow(CoherencyEvaluator, SycophancyDataGenerator):
    model = Mock()
    model.meta.name = "Test Model"
    model.meta.description = "Test Description"

    dataset = Mock(column_types=sentinel.coltypes)

    generator = Mock()
    evaluator = Mock()
    SycophancyDataGenerator.return_value = generator
    CoherencyEvaluator.return_value = evaluator

    eval_dataset_1 = Dataset(pd.DataFrame({"feat": ["input 1"]}))
    eval_dataset_2 = Dataset(pd.DataFrame({"feat": ["input 2"]}))
    generator.generate_dataset.return_value = (eval_dataset_1, eval_dataset_2)
    evaluator.evaluate.side_effect = [
        EvaluationResult(
            results=[
                EvaluationResultExample(
                    sample={"conversation": []}, reason="Test reason", status=TestResultStatus.PASSED
                )
            ]
        ),
        EvaluationResult(
            results=[
                EvaluationResultExample(
                    sample={"conversation": []}, reason="Test reason 2", status=TestResultStatus.FAILED
                )
            ]
        ),
    ]

    detector = LLMBasicSycophancyDetector(num_samples=13892)
    issues = detector.run(model, dataset)

    assert len(issues) == 0
    generator.generate_dataset.assert_called_once_with(model, num_samples=13892, column_types=sentinel.coltypes)
    evaluator.evaluate.assert_called_once_with(model, eval_dataset_1, eval_dataset_2)

    issues = detector.run(model, dataset)
    assert len(issues) == 1
    assert issues[0].generate_tests()[0]
    assert issues[0].dataset == eval_dataset_2

    # Issues must contain the "metric" name
    assert "metric" in issues[0].meta
    assert "metric_value" in issues[0].meta
