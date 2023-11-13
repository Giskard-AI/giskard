import re
import string
import logging
from typing import Tuple, Dict
from dataclasses import dataclass


from .base import BaseEvaluator, EvaluationResult
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..errors import LLMGenerationError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class StringMatchingMethod:
    substrings: Tuple[str]
    all_substrings_must_be_found: bool = True
    exact_matching: bool = False
    word_matching: bool = False
    case_sensitive: bool = True
    punctuation_sensitive: bool = True
    evaluation_method_name: str = "StringMatchingMethod"


def get_evaluation_method_from_meta(kwargs: Dict):
    kwargs = {k: v for k, v in kwargs.items() if k in list(StringMatchingMethod.__annotations__.keys())}

    return StringMatchingMethod(**kwargs)


class StringMatcher(BaseEvaluator):
    @staticmethod
    def normalize_text(text, case_sensitive, punctuation_sensitive):
        if not case_sensitive:
            text = text.lower()
        if not punctuation_sensitive:
            text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    @staticmethod
    def evaluate_substring(substring, prediction, exact_matching, word_matching):
        if exact_matching:
            return substring == prediction
        if word_matching:
            return re.search(r"\b" + re.escape(substring) + r"\b", prediction) is not None
        return substring in prediction

    @staticmethod
    def _evaluate(prediction: str, evaluation_method):
        failed = 0
        for s in evaluation_method.substrings:
            normalized_s = StringMatcher.normalize_text(
                s, evaluation_method.case_sensitive, evaluation_method.punctuation_sensitive
            )
            normalized_prediction = StringMatcher.normalize_text(
                prediction, evaluation_method.case_sensitive, evaluation_method.punctuation_sensitive
            )
            if StringMatcher.evaluate_substring(
                normalized_s, normalized_prediction, evaluation_method.exact_matching, evaluation_method.word_matching
            ):
                failed += 1

        if evaluation_method.all_substrings_must_be_found:
            failed = 1 if failed == len(evaluation_method.substrings) else 0
        else:
            failed = 1 if failed != 0 else 0

        return failed

    def evaluate(self, model: BaseModel, dataset: Dataset, evaluator_config):
        model_outputs = model.predict(dataset).prediction

        succeeded = []
        failed = []
        errored = []
        zipped = zip(dataset.df.loc[:, model.meta.feature_names].to_dict("records"), model_outputs)

        for i, items in enumerate(zipped):
            input_vars, model_output = items[0], items[1]
            try:
                if not evaluator_config[i].get("substrings", None):
                    raise ValueError(
                        f"{self.__class__.__name__}: substrings for {input_vars} are needed for the evaluation."
                    )
                evaluation_method = get_evaluation_method_from_meta(evaluator_config[i])

                prompt_failed = self._evaluate(model_output, evaluation_method=evaluation_method)
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": input_vars})
                continue
            if not prompt_failed:
                succeeded.append({"input_vars": input_vars, "model_output": model_output})
            else:
                failed.append({"input_vars": input_vars, "model_output": model_output})

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeeded,
            errors=errored,
        )
