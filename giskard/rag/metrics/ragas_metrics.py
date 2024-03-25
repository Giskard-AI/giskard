from typing import Sequence, Union

import logging

from datasets import Dataset

from ...llm.client import LLMClient, LLMMessage
from ..testset import QATestset
from .base import Metric

logger = logging.getLogger(__name__)

try:
    from langchain_core.outputs import LLMResult
    from langchain_core.outputs.generation import Generation
    from ragas import evaluate
    from ragas.embeddings import BaseRagasEmbeddings
    from ragas.llms import BaseRagasLLM
    from ragas.llms.prompt import PromptValue
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.metrics.base import Metric as BaseRagasMetric

except ImportError as err:
    logger.error(
        f"Package {err.name} is missing, it is required for the computation of RAGAS metrics. You can install it with `pip install {err.name}`."
    )


class RagasLLMWrapper(BaseRagasLLM):
    def __init__(self, llm_client, context_window_length: int):
        self.llm_client = llm_client
        self.context_window_length = context_window_length

    def trim_prompt(self, prompt: str) -> str:
        return prompt[: int(self.context_window_length * 3.5)]

    def generate_text(self, prompt: PromptValue, n: int = 1, temperature: float = 1e-8, stop=None, callbacks=[]):
        out = self.llm_client.complete([LLMMessage(role="user", content=self.trim_prompt(prompt.to_string()))])
        return LLMResult(generations=[[Generation(text=out.content)]])

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float = 1e-8,
        stop: Sequence[str] | None = None,
        callbacks=[],
    ):
        return self.generate_text(prompt, n, temperature, stop, callbacks)


class RagasEmbeddingsWrapper(BaseRagasEmbeddings):
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def embed_query(self, text: str) -> Sequence[float]:
        return self.llm_client.embeddings([text])[0]

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return self.llm_client.embeddings(texts)


class RagasMetric(Metric):
    """
    A wrapper for RAGAS metrics, so they can be used inside the `~giskard.rag.evaluate` function.

    Parameters
    ----------
    name : str
        The name of the metric.
    metrics : Union[BaseRagasMetric, Sequence[BaseRagasMetric]]
        The list of RAGAS metrics to use.
    """

    def __init__(
        self, name: str, metrics: Union[BaseRagasMetric, Sequence[BaseRagasMetric]], context_window_length: int = 8192
    ) -> None:
        self.name = name
        self.metrics = metrics if isinstance(metrics, Sequence) else [metrics]
        self.context_window_length = context_window_length

    def __call__(self, testset: QATestset, answers: Sequence[str], llm_client: LLMClient) -> dict:
        ragas_llm = RagasLLMWrapper(llm_client, self.context_window_length)
        ragas_embedddings = RagasEmbeddingsWrapper(llm_client)

        testset_df = testset.to_pandas().copy()
        testset_df["answer"] = answers
        testset_df.rename(columns={"reference_context": "contexts", "reference_answer": "ground_truth"}, inplace=True)
        testset_df["contexts"] = testset_df["contexts"].apply(lambda x: x.split("\n------\n"))
        dataset = Dataset.from_pandas(testset_df[["question", "ground_truth", "contexts", "answer"]])

        ragas_metrics_df = evaluate(
            dataset,
            metrics=self.metrics,
            llm=ragas_llm,
            embeddings=ragas_embedddings,
        ).to_pandas()

        ragas_metrics_df = ragas_metrics_df.rename(
            columns={metric.name: f"{self.name}_{metric.name}" for metric in self.metrics}
        )
        ragas_metrics_result = {
            f"{self.name}_{metric.name}": ragas_metrics_df[["id", f"{self.name}_{metric.name}"]].set_index("id")
            for metric in self.metrics
        }
        return ragas_metrics_result


ragas_context_precision = RagasMetric(name="RAGAS Context Precision", metrics=context_precision)
ragas_faithfulness = RagasMetric(name="RAGAS Faithfulness", metrics=faithfulness)
ragas_answer_relevancy = RagasMetric(name="RAGAS Answer Relevancy", metrics=answer_relevancy)
ragas_context_recall = RagasMetric(name="RAGAS Context Recall", metrics=context_recall)
