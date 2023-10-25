import re
import string
import logging
from abc import ABC
from colorama import Fore, Style

from .data import Prompt, StringMatchingMethod

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Evaluator(ABC):
    """Base class for evaluators that define a way of detecting a LLM failure"""

    def __init__(self, name: str = None):
        if name is None:
            self.name = __class__

        print(f"loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}Evaluator{Style.RESET_ALL}: {self.name}")
        logger.info(f"Evaluator init: {self}")

    @staticmethod
    def evaluate(prediction: str, prompt: Prompt) -> bool:
        """Takes a prediction and a prompt and returns 1 if vulnerability is found."""
        raise NotImplementedError


class StringMatcher(Evaluator):
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
    def evaluate(prediction: str, prompt: Prompt) -> int:
        failed = 0
        evaluation_method = prompt.evaluation_method

        if not isinstance(evaluation_method, StringMatchingMethod):
            raise ValueError("The prompt's evaluation method does not match the evaluator chosen")

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


def evaluate(prediction: str, prompt: Prompt):
    if isinstance(prompt.evaluation_method, StringMatchingMethod):
        return StringMatcher.evaluate(prediction, prompt)
    raise NotImplementedError(f"No evaluator is currently implemented for {prompt.evaluation_method}.")
