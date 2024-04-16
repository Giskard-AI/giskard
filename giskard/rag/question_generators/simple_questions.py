import uuid

from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator
from .prompt import QAGenerationPrompt

QA_GENERATION_SYSTEM_PROMPT = """You are a powerful auditor, your role is to generate question & answer pair from a given list of context paragraphs.

The agent model you are auditing is the following:
- Agent description: {agent_description}

Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found inside the provided context
- The question must be self-contained
- The question and answer must be in this language: {language}

The user will provide the context, consisting in multiple paragraphs delimited by dashes "------".
You will return the question and the precise answer to the question based exclusively on the provided context.
You must output a single JSON object with keys 'question' and 'answer', without any other wrapping text or markdown. Make sure you only return valid JSON. """


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


class SimpleQuestionsGenerator(GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator):
    """
    Base question generator that generates questions from a KnowledgeBase.

    Parameters
    ----------
    context_neighbors: int, optional
        Number of context neighbors to use for question generation.
    context_similarity_threshold: float, optional
        Similarity threshold to keep neighboring document during question generation.
    context_window_length: int, optional
        Context window length of the llm used in the `llm_client` of the generator.
    llm_client: LLMClient, optional
        The LLM client to use for question generation. If not specified, a default openai client will be used.
    llm_temperature: float, optional
        The temperature to use in the LLM for question generation. The default is 0.5.
    """

    _prompt = QAGenerationPrompt(
        system_prompt=QA_GENERATION_SYSTEM_PROMPT,
        example_input=QA_GENERATION_EXAMPLE_INPUT,
        example_output=QA_GENERATION_EXAMPLE_OUTPUT,
    )

    _question_type = "simple"

    def generate_single_question(self, knowledge_base: KnowledgeBase, agent_description: str, language: str) -> dict:
        """
        Generate a question from a list of context documents.

        Parameters
        ----------
        context_documents : Sequence[Document]
            The context documents to generate the question from.

        Returns
        -------
        QuestionSample
            The generated question and the metadata of the question.
        """
        seed_document = knowledge_base.get_random_document()
        context_documents = knowledge_base.get_neighbors(
            seed_document, self._context_neighbors, self._context_similarity_threshold
        )
        context_str = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])

        reference_context = "\n\n".join([f"Document {doc.id}: {doc.content}" for doc in context_documents])

        messages = self._prompt.to_messages(
            system_prompt_input={"agent_description": agent_description, "language": language},
            user_input=context_str,
        )

        generated_qa = self._llm_complete(messages=messages)
        question_metadata = {"question_type": self._question_type, "seed_document_id": seed_document.id}

        question = QuestionSample(
            id=str(uuid.uuid4()),
            question=generated_qa["question"],
            reference_answer=generated_qa["answer"],
            reference_context=reference_context,
            conversation_history=[],
            metadata=question_metadata,
        )
        return question


simple_questions = SimpleQuestionsGenerator()
