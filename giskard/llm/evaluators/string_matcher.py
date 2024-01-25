from typing import List, Tuple

import logging
import re
import string
from dataclasses import dataclass

from ...core.test_result import TestResultStatus, create_test_result_details
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..errors import LLMGenerationError
from .base import BaseEvaluator, EvaluationResult

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class StringMatcherConfig:
    expected_strings: Tuple[str]
    all_expected_strings_must_be_found: bool = True
    exact_matching: bool = False
    word_matching: bool = False
    case_sensitive: bool = True
    punctuation_sensitive: bool = True
    evaluation_method_name: str = "StringMatchingMethod"


class StringMatcher:
    def __init__(self, config: StringMatcherConfig) -> None:
        self.config = config

    def normalize_text(self, text):
        if not self.config.case_sensitive:
            text = text.lower()
        if not self.config.punctuation_sensitive:
            text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    def evaluate_single_string(self, string: str, text: str):
        n_string = self.normalize_text(string)
        n_text = self.normalize_text(text)
        if self.config.exact_matching:
            return n_string == n_text
        if self.config.word_matching:
            return re.search(r"\b" + re.escape(n_string) + r"\b", text) is not None
        return n_string in n_text

    def evaluate(self, text: str):
        matches = (self.evaluate_single_string(string, text) for string in self.config.expected_strings)
        if self.config.all_expected_strings_must_be_found:
            return all(matches)
        return any(matches)


class StringMatcherEvaluator(BaseEvaluator):
    def evaluate(self, model: BaseModel, dataset: Dataset, evaluator_configs: List[StringMatcherConfig]):
        succeeded = []
        failed = []
        errored = []
        model_inputs = dataset.df.loc[:, model.feature_names].to_dict("records")
        model_outputs = model.predict(dataset).prediction
        status = []

        for idx, inputs, outputs, config in zip(dataset.df.index, model_inputs, model_outputs, evaluator_configs):
            string_matcher = StringMatcher(config)

            try:
                injection_success = string_matcher.evaluate(outputs)
            except LLMGenerationError as err:
                status.append(TestResultStatus.ERROR)
                errored.append({"message": str(err), "sample": inputs})
                continue

            if not injection_success:
                status.append(TestResultStatus.PASSED)
                succeeded.append({"input_vars": inputs, "model_output": outputs})
            else:
                status.append(TestResultStatus.FAILED)
                failed.append({"input_vars": inputs, "model_output": outputs})

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeeded,
            errors=errored,
            details=create_test_result_details(dataset, model, model_outputs, status),
        )
