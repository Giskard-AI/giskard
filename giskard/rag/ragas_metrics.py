from typing import List

import pandas as pd
from datasets import Dataset
from langchain_core.outputs import LLMResult
from langchain_core.outputs.generation import Generation
from ragas import evaluate
from ragas.embeddings import BaseRagasEmbeddings
from ragas.llms import BaseRagasLLM
from ragas.llms.prompt import PromptValue
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from ..llm.client import LLMClient, LLMMessage
from .testset import QATestset


class RagasLLMWrapper(BaseRagasLLM):
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_text(self, prompt: PromptValue, n: int = 1, temperature: float = 1e-8, stop=None, callbacks=[]):
        out = self.llm_client.complete([LLMMessage(role="user", content=prompt.to_string())])
        return LLMResult(generations=[[Generation(text=out.content)]])

    async def agenerate_text(
        self, prompt: PromptValue, n: int = 1, temperature: float = 1e-8, stop: List[str] | None = None, callbacks=[]
    ):
        return self.generate_text(prompt, n, temperature, stop, callbacks)


class RagasEmbeddingsWrapper(BaseRagasEmbeddings):
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def embed_query(self, text: str) -> List[float]:
        return self.llm_client.embeddings([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.llm_client.embeddings(texts)


def compute_ragas_metrics(
    testset: QATestset,
    answers: List[str],
    gsk_llm_client: LLMClient,
) -> pd.DataFrame:
    pass

    ragas_llm = RagasLLMWrapper(gsk_llm_client)
    ragas_embedddings = RagasEmbeddingsWrapper(gsk_llm_client)

    testset_df = testset.to_pandas().copy()
    testset_df["answer"] = answers
    testset_df.rename(columns={"reference_context": "contexts", "reference_answer": "ground_truth"}, inplace=True)
    testset_df["contexts"] = testset_df["contexts"].apply(lambda x: x.split("\n------\n"))
    ragas_dataset = Dataset.from_pandas(testset_df[["question", "ground_truth", "contexts", "answer"]])

    return evaluate(
        ragas_dataset,
        metrics=[
            context_precision,
            faithfulness,
            answer_relevancy,
            context_recall,
        ],
        llm=ragas_llm,
        embeddings=ragas_embedddings,
    ).to_pandas()
