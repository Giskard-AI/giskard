from abc import ABC, abstractmethod

from ...llm.client.base import LLMClient
from ..base import AgentAnswer


class Metric(ABC):
    """
    Metric base class. All metrics should inherit from this class and implement the __call__ method.
    The instances of this class can be passed to the evaluate method.
    """

    def __init__(self, name: str, llm_client: LLMClient = None) -> None:
        self.name = name
        self._llm_client = llm_client

    @abstractmethod
    def __call__(self, question_sample: dict, answer: AgentAnswer):
        """
        Compute the metric on a single question and its associated answer.

        Parameters
        ----------
        question_sample : dict
            A question sample from a QATestset.
        answer : AgentAnswer
            The agent answer on that question.

        Returns
        -------
        dict
            The result of the metric computation. The keys should be the names of the metrics computed.
        """
        pass
