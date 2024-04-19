from typing import Optional, Sequence

import logging

import nest_asyncio

from ...llm.client import ChatMessage, LLMClient, get_default_client
from .base import Metric

nest_asyncio.apply()
logger = logging.getLogger(__name__)

try:
    from langchain_core.outputs import LLMResult
    from langchain_core.outputs.generation import Generation
    from ragas.embeddings import BaseRagasEmbeddings
    from ragas.llms import BaseRagasLLM
    from ragas.llms.prompt import PromptValue
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.metrics.base import Metric as BaseRagasMetric
    from ragas.run_config import RunConfig

except ImportError as err:
    raise ImportError(
        f"Package {err.name} is missing, it is required for the computation of RAGAS metrics. You can install it with `pip install {err.name}`."
    ) from err


class RagasLLMWrapper(BaseRagasLLM):
    def __init__(self, llm_client, context_window_length: int):
        self.llm_client = llm_client
        self.context_window_length = context_window_length

    def trim_prompt(self, prompt: str) -> str:
        return prompt[: int(self.context_window_length * 3.5)]

    def generate_text(self, prompt: PromptValue, n: int = 1, temperature: float = 1e-8, stop=None, callbacks=[]):
        out = self.llm_client.complete([ChatMessage(role="user", content=self.trim_prompt(prompt.to_string()))])
        return LLMResult(generations=[[Generation(text=out.content)]])

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float = 1e-8,
        stop: Optional[Sequence[str]] = None,
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
    def __init__(
        self, name: str, metric: BaseRagasMetric, context_window_length: int = 8192, llm_client: LLMClient = None
    ) -> None:
        self.name = name
        self.metric = metric
        self.context_window_length = context_window_length
        self._llm_client = llm_client

    def __call__(self, question_sample: dict, answer: str) -> dict:
        llm_client = self._llm_client or get_default_client()
        ragas_llm = RagasLLMWrapper(llm_client, self.context_window_length)
        ragas_embedddings = RagasEmbeddingsWrapper(llm_client)

        run_config = RunConfig()

        if hasattr(self.metric, "llm"):
            self.metric.llm = ragas_llm
        if hasattr(self.metric, "embeddings"):
            self.metric.embeddings = ragas_embedddings

        self.metric.init(run_config)

        ragas_sample = {
            "question": question_sample["question"],
            "answer": answer,
            "contexts": question_sample["reference_context"].split("\n\n"),
            "ground_truth": question_sample["reference_answer"],
        }
        return {self.name: self.metric.score(ragas_sample)}


ragas_context_precision = RagasMetric(name="RAGAS Context Precision", metric=context_precision)
ragas_faithfulness = RagasMetric(name="RAGAS Faithfulness", metric=faithfulness)
ragas_answer_relevancy = RagasMetric(name="RAGAS Answer Relevancy", metric=answer_relevancy)
ragas_context_recall = RagasMetric(name="RAGAS Context Recall", metric=context_recall)
