from typing import Optional, Sequence

import json
import logging

from ...llm.client import get_default_client
from ...llm.client.base import LLMClient, LLMMessage
from ..knowledge_base import Document, KnowledgeBase
from .prompt import QAGenerationPrompt
from .question_types import QuestionTypes

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


class SimpleQuestionsGenerator:
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        language: str = "en",
        assistant_description: str = "This assistant is a chatbot that answers question from users.",
        context_window_length: int = 8192,
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.5,
    ):
        self._knowledge_base = knowledge_base
        self._language = language
        self._assistant_description = assistant_description
        self._context_window_length = context_window_length
        self._llm_client = llm_client or get_default_client()
        self._llm_temperature = llm_temperature

        self._prompt = QAGenerationPrompt(
            system_prompt=QA_GENERATION_SYSTEM_PROMPT,
            example_input=QA_GENERATION_EXAMPLE_INPUT,
            example_output=QA_GENERATION_EXAMPLE_OUTPUT,
        )

    def _llm_complete(self, messages: Sequence[LLMMessage]) -> dict:
        try:
            out = self._llm_client.complete(
                messages=messages,
                temperature=0.5,
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

    def generate_question(self, context_documents: Sequence[Document]) -> dict:
        context = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])
        messages = self._prompt.to_messages(
            system_prompt_input={"assistant_description": self._assistant_description, "language": self._language},
            user_input=context,
        )

        generated_qa = self._llm_complete(messages=messages)
        question_metadata = {"question_type": QuestionTypes.EASY.value, "reference_context": context}

        return generated_qa, question_metadata
