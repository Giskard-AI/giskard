from typing import Optional, Sequence

import logging

from ...llm.client import ChatMessage, LLMClient, get_default_client
from ...llm.embeddings import BaseEmbedding, get_default_embedding
from ..base import AgentAnswer
from .base import Metric

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


try:
    # RAGAS has async functions, we try to apply nest_asyncio to avoid issues in notebooks
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    pass


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
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def embed_query(self, text: str) -> Sequence[float]:
        return self.embedding_model.embed([text])[0]

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return self.embedding_model.embed(texts)


class RagasMetric(Metric):
    def __init__(
        self,
        name: str,
        metric: BaseRagasMetric,
        context_window_length: int = 8192,
        llm_client: LLMClient = None,
        embedding_model: BaseEmbedding = None,
        requires_context=False,
    ) -> None:
        self.name = name
        self.metric = metric
        self.context_window_length = context_window_length
        self._llm_client = llm_client
        self._embedding_model = embedding_model
        self.requires_context = requires_context
        self.ragas_llm = None
        self.ragas_embeddings = None

    def __call__(self, question_sample: dict, answer: AgentAnswer) -> dict:
        llm_client = self._llm_client or get_default_client()
        embedding_model = self._embedding_model or get_default_embedding()
        if self.ragas_llm is None:
            self.ragas_llm = RagasLLMWrapper(llm_client, self.context_window_length)
        if self.ragas_embeddings is None:
            self.ragas_embeddings = RagasEmbeddingsWrapper(embedding_model)

        run_config = RunConfig()

        if hasattr(self.metric, "llm"):
            self.metric.llm = self.ragas_llm
        if hasattr(self.metric, "embeddings"):
            self.metric.embeddings = self.ragas_embeddings

        self.metric.init(run_config)
        if self.requires_context and answer.documents is None:
            logger.warn(
                f"No retrieved documents are passed to the evaluation function, computation of {self.name} cannot be done without it."
                "Make sure you pass 'retrieved_documents' to the evaluate function or that the 'answer_fn' return documents alongside the answer."
            )
            return {self.name: 0}

        ragas_sample = {
            "question": question_sample["question"],
            "answer": answer.message,
            "contexts": answer.documents,
            "ground_truth": question_sample["reference_answer"],
        }
        return {self.name: self.metric.score(ragas_sample)}


ragas_context_precision = RagasMetric(name="RAGAS Context Precision", metric=context_precision, requires_context=True)
ragas_faithfulness = RagasMetric(name="RAGAS Faithfulness", metric=faithfulness, requires_context=True)
ragas_answer_relevancy = RagasMetric(name="RAGAS Answer Relevancy", metric=answer_relevancy, requires_context=True)
ragas_context_recall = RagasMetric(name="RAGAS Context Recall", metric=context_recall, requires_context=True)
