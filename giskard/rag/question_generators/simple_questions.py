from typing import Optional, Sequence

import json
import logging

import numpy as np
import pandas as pd

from ...llm.client import get_default_client
from ...llm.client.base import LLMClient, LLMMessage
from ..vector_store import Document, VectorStore
from .prompt import QAGenerationPrompt
from .utils import DifficultyLevel

logger = logging.getLogger(__name__)


QA_GENERATION_SYSTEM_PROMPT = """You are a powerful auditor, your role is to generate question & answer pair from a given list of context paragraphs.

The assistant model you are auditing is the following:
- Assistant description: {assistant_description}

Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found inside the provided context
- The question must be self-contained
- The question and answer must be in this language: {language}

The user will provide the context, consisting in multiple paragraphs delimited by dashes "------".
You will return the question and the precise answer to the question based exclusively on the provided context.
You must output a single JSON object with keys 'question' and 'answer'. Make sure you return a valid JSON object."""


QA_GENERATION_EXAMPLE_INPUT = """What payment methods do you accept?

We accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
"""

QA_GENERATION_EXAMPLE_OUTPUT = """{
    "question": "For which countries can I track my shipping?",
    "answer": "We ship to all 50 states in the US, as well as to Canada and Mexico. We offer tracking for all our shippings."
}"""


class SimpleQuestionGenerator:
    def __init__(
        self,
        knowledge_base: pd.DataFrame,
        knowledge_base_columns: Sequence[str] = None,
        language: str = "en",
        assistant_description: str = "This assistant is a chatbot that answers question from users.",
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        seed: int = None,
        include_examples: bool = True,
        embedding_model: str = "text-embedding-ada-002",
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.5,
    ):
        self._knowledge_base = knowledge_base
        self._knowledge_base_columns = knowledge_base_columns
        self._language = language
        self._assistant_description = assistant_description
        self._context_neighbors = context_neighbors
        self._context_similarity_threshold = context_similarity_threshold
        self._embedding_model = embedding_model
        self._context_window_length = context_window_length
        self._rng = np.random.default_rng(seed=seed)
        self._include_examples = include_examples
        self._vector_store_inst = None
        self._llm_client = llm_client or get_default_client()
        self._llm_temperature = llm_temperature

        self.prompt = QAGenerationPrompt(
            system_prompt=QA_GENERATION_SYSTEM_PROMPT,
            example_input=QA_GENERATION_EXAMPLE_INPUT,
            example_output=QA_GENERATION_EXAMPLE_OUTPUT,
        )

    @property
    def _vector_store(self):
        if self._vector_store_inst is None:
            logger.debug("Initializing vector store from knowledge base.")
            self._vector_store_inst = VectorStore.from_df(
                self._knowledge_base,
                lambda query: self._llm_client.embeddings(query, model=self._embedding_model),
                features=self._knowledge_base_columns,
            )
        return self._vector_store_inst

    def _get_random_document_group(self):
        seed_embedding = self._rng.choice(self._vector_store.embeddings)
        relevant_contexts = [
            context
            for (context, score) in self._vector_store.vector_similarity_search_with_score(
                seed_embedding, k=self._context_neighbors
            )
            if score < self._context_similarity_threshold
        ]

        return relevant_contexts

    def _prevent_context_window_overflow(self, prompt: str):
        # Prevent context overflow
        # general rule of thumbs to count tokens: 1 token ~ 4 characters
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        return prompt[: self._context_window_length * 4]

    def _llm_complete(self, messages: Sequence[dict]) -> dict:
        try:
            out = self._llm_client.complete(
                messages=messages,
                temperature=self._llm_temperature,
                caller_id=self.__class__.__name__,
            )

            return json.loads(out.content, strict=False)
        except json.decoder.JSONDecodeError:
            logger.warning("JSON decoding error, trying to fix the JSON string.")
            return self._try_fix_json_message(out.content)

    def _try_fix_json_message(self, incorrect_json: str):
        out = self._llm_client.complete(
            messages=[
                LLMMessage(
                    role="system",
                    content="Fix the following json string so it contains a single valid json. Make sure to start and end with curly brackets.",
                ),
                LLMMessage(role="user", content=incorrect_json),
            ],
            temperature=0,
            caller_id=self.__class__.__name__,
        )
        return json.loads(out.content)

    def _generate_question(self, context_documents: Sequence[Document]) -> dict:
        context = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])
        messages = self.prompt.to_messages(
            assistant_description=self._assistant_description,
            language=self._language,
            user_input=context,
        )

        generated_qa = self._llm_complete(messages=messages)
        question_metadata = {"difficulty": DifficultyLevel.EASY, "reference_context": context}

        return generated_qa, question_metadata
