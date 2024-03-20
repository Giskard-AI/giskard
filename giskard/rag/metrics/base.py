from typing import Sequence

from abc import ABC, abstractmethod

from ..testset import QATestset


class Metric(ABC):
    """
    Metric base class. All metrics should inherit from this class and implement the __call__ method.
    The instances of this class can be passed to the evaluate method.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def __call__(self, testset: QATestset, answers: Sequence[str], *args, **kwargs):
        """
        Compute the metric on the test set and the answers.

        Parameters
        ----------
        testset : QATestset
            The test set to compare the answers with.
        answers : Sequence[str]
            The answers of the agent to evaluate.

        Returns
        -------
        dict
            The result of the metric. The keys should be the name of the metrics and the
            values should be the result of the metric for each question/answer pair.
        """
        pass
