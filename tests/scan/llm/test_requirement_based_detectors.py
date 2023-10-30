from unittest.mock import Mock, patch

import pandas as pd
import pytest

from giskard import Dataset
from giskard.llm.client import LLMOutput
from giskard.llm.evaluators.base import EvaluationResult
from giskard.scanner.llm.llm_harmful_content_detector import LLMHarmfulContentDetector
from giskard.scanner.llm.llm_information_disclosure_detector import LLMInformationDisclosure
from giskard.scanner.llm.llm_output_format_detector import LLMOutputFormattingDetector
from giskard.scanner.llm.llm_stereotypes_detector import LLMStereotypesDetector


@pytest.mark.parametrize(
    "Detector,issue_match",
    [
        (LLMStereotypesDetector, "Stereotypes & Discrimination"),
        (LLMInformationDisclosure, "Disclosure of Sensitive Information"),
        (LLMHarmfulContentDetector, "Generation of Harmful Content"),
        (LLMOutputFormattingDetector, "Output formatting"),
    ],
)
def test_requirement_based_detector_flow(Detector, issue_match):
    with (
        patch("giskard.scanner.llm.base.TestcaseRequirementsGenerator") as TestcaseRequirementsGenerator,
        patch("giskard.scanner.llm.base.AdversarialDataGenerator") as AdversarialDataGenerator,
        patch("giskard.scanner.llm.base.RequirementEvaluator") as RequirementEvaluator,
        patch("giskard.scanner.llm.llm_output_format_detector.get_default_client") as get_default_client,
    ):
        # For output format detector
        llm_client = Mock()
        get_default_client.return_value = llm_client
        llm_client.complete.return_value = LLMOutput(message="y")

        model = Mock()
        model.meta.name = "Test Model"
        model.meta.description = "Test Description"

        requirements_generator = Mock()

        TestcaseRequirementsGenerator.return_value = requirements_generator
        requirements_generator.generate_requirements.return_value = ["Requirement One", "Requirement Two"]

        adv_gen_1 = Mock()
        adv_gen_2 = Mock()
        AdversarialDataGenerator.side_effect = [adv_gen_1, adv_gen_2]

        dataset_1 = Dataset(pd.DataFrame({"feat": ["input 1", "input 2", "input 3"]}))
        dataset_2 = Dataset(pd.DataFrame({"feat": ["test 1", "test 2", "test 3"]}))
        adv_gen_1.generate_dataset.return_value = dataset_1
        adv_gen_2.generate_dataset.return_value = dataset_2

        eval_1 = Mock()
        eval_2 = Mock()
        RequirementEvaluator.side_effect = [eval_1, eval_2]

        eval_1.evaluate.return_value = EvaluationResult(
            failure_examples=[], success_examples=[{"sample": 1}], errors=[]
        )
        eval_2.evaluate.return_value = EvaluationResult(
            failure_examples=[{"value_1": "test 1", "value_2": "output 1"}], success_examples=[], errors=[]
        )

        detector = Detector(num_requirements=2, num_samples=3)
        issues = detector.run(model, Mock())

        assert len(issues) == 1
        assert issues[0].generate_tests()[0]
        assert issues[0].dataset == dataset_2

        # Requirements generation
        TestcaseRequirementsGenerator.assert_called_once()
        assert issue_match in TestcaseRequirementsGenerator.call_args[0][0]

        requirements_generator.generate_requirements.assert_called_once_with(model, 2)

        # Examples generation
        AdversarialDataGenerator.call_args_list[0].kwargs["requirement"] == "Requirement One"
        AdversarialDataGenerator.call_args_list[1].kwargs["requirement"] == "Requirement Two"

        adv_gen_1.generate_dataset.assert_called_once_with(model, 3)
        adv_gen_2.generate_dataset.assert_called_once_with(model, 3)
