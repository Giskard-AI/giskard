import re
import string
import logging
from typing import Tuple, List
from dataclasses import dataclass

from .base import BaseEvaluator, EvaluationResult
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..errors import LLMGenerationError

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
        model_outputs = model.predict(dataset).prediction

        succeeded = []
        failed = []
        failed_indices = []
        errored = []
        model_inputs = dataset.df.loc[:, model.meta.feature_names].to_dict("records")

        for i_pos, i_idx in enumerate(dataset.df.index):
            string_matcher = StringMatcher(evaluator_configs[i_pos])
            model_output = model_outputs[i_pos]
            model_input = model_inputs[i_pos]

            try:
                injection_success = string_matcher.evaluate(model_output)
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": model_input[i_pos]})
                continue

            if not injection_success:
                succeeded.append({"input_vars": model_input, "model_output": model_output})
            else:
                failed.append({"input_vars": model_input, "model_output": model_output})
                failed_indices.append(i_idx)

        return EvaluationResult(
            failure_examples=failed,
            failed_indices=failed_indices,
            success_examples=succeeded,
            errors=errored,
        )
