import re
import string
from abc import ABC, abstractmethod
from colorama import Fore, Style

from ...scanner import logger
from .data import Prompt, StringMatchingMethod


class Evaluator(ABC):
    """Base class for evaluators that define a way of detecting a LLM failure"""

    def __init__(self, name: str = None):
        if name is None:
            self.name = __class__

        print(f"loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}Evaluator{Style.RESET_ALL}: {self.name}")
        logger.info(f"Evaluator init: {self}")

    @abstractmethod
    def evaluate(self, prediction: str, prompt: Prompt) -> bool:
        """Takes a prediction and a prompt and returns 1 if vulnerability is found."""
        raise NotImplementedError


class StringMatcher(Evaluator):
    @staticmethod
    def evaluate(prediction: str, prompt: Prompt) -> bool:
        failed = 0
        evaluation_method = prompt.evaluation_method
        if not isinstance(evaluation_method, StringMatchingMethod):
            raise ValueError("The prompt's evaluation method does not match the evaluator chosen")

        for s in evaluation_method.substrings:
            if not evaluation_method.case_sensitive:
                s, prediction = s.lower(), prediction.lower()

            if not evaluation_method.punctuation_sensitive:
                s = s.translate(str.maketrans("", "", string.punctuation))
                prediction = prediction.translate(str.maketrans("", "", string.punctuation))

            if evaluation_method.exact_matching:
                if s == prediction:
                    failed = 1
            else:
                if evaluation_method.word_matching:
                    if re.search(r"\b" + s + r"\b", prediction):
                        failed = 1
                else:
                    if s in prediction:
                        failed = 1
        return failed


def evaluate(prediction: str, prompt: Prompt):
    if isinstance(prompt.evaluation_method, StringMatchingMethod):
        return StringMatcher.evaluate(prediction, prompt)
    raise NotImplementedError(f"No evaluator is currently implemented for {prompt.evaluation_method}.")
