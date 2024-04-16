from abc import ABC, abstractmethod

from ...llm.client.base import LLMClient


class Metric(ABC):
    """
    Metric base class. All metrics should inherit from this class and implement the __call__ method.
    The instances of this class can be passed to the evaluate method.
    """

    def __init__(self, name: str, llm_client: LLMClient = None) -> None:
        self.name = name
        self._llm_client = llm_client

    @abstractmethod
    def __call__(self, question_sample: dict, answer: str):
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
