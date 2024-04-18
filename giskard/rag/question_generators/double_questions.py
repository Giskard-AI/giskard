import uuid

from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator
from .prompt import QAGenerationPrompt

LINKED_QUESTION_SYSTEM_PROMPT = """You are a powerful auditor, your role is to generate two question & answer pairs from a given list of context paragraphs.

The agent you are auditing is the following:
- Assitant description: {agent_description}

Your questions must be related to the provided context.  
Please respect the following rules to generate the question:
- The answers to the questions should be found inside the provided context
- Each question must be self-contained.
- Each question and answer pair must be coherent by itself and in agreement with the provided context
- The two questions and answers pairs must be about slightly different topics.
- The questions and answers must be in this language: {language}

The user will provide the context, consisting in multiple paragraphs delimited by dashes "------".
You must output a list of exactly two JSON objects with keys 'question' and 'answer'. Make sure you return a valid JSON object."""

LINKED_QUESTION_EXAMPLE_INPUT = """What payment methods do you accept?

We accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
"""

LINKED_QUESTION_EXAMPLE_OUTPUT = """[
    {"question": "What payment methods do you accept?", "answer": "We accept a variety of payment methods to provide our customers with a convenient and secure shopping experience."},
    {"question": "What is your shipping policy?", "answer": "We offer free shipping on all orders over $50."}
}]"""


DOUBLE_QUESTION_SYSTEM_PROMPT = """You are an expert at rewriting questions.
Your task is to combine two questions and answer pairs into a single one.

Please respect the following rules to generate the double question:
- The combined question must ask the exact same information as the two provided question.
- The question must be formulated as a double question, with two sentence linked into one.
- The answer of the double question must summarize the two provided answers.
- The question and answer must be in this language: {language}.

The two question and answer pairs will be provided to you separated with dashes "---------".

You will return the double question and the associated answer.
Your output should be a single JSON object, with keys 'question' and 'answer'. Make sure you return a valid JSON object.
"""

DOUBLE_QUESTION_USER_TEMPLATE = """<question1>{question_1}</question1>
<answer1>{answer_1}</answer1>
---------
<question2>{question_2}</question2>
<answer2>{answer_2}</answer2>
"""

DOUBLE_QUESTION_EXAMPLE_INPUT = DOUBLE_QUESTION_USER_TEMPLATE.format(
    question_1="What is the capital of France?",
    answer_1="The capital of France is Paris.",
    question_2="What is the currency of France?",
    answer_2="The currency of France is the Euro.",
)

DOUBLE_QUESTION_EXAMPLE_OUTPUT = """{
    "question": "What is the capital and currency of France?",
    "answer": "The capital of France is Paris and the currency is the Euro."
}"""


class DoubleQuestionsGenerator(GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator):
    _linked_question_generation_prompt = QAGenerationPrompt(
        system_prompt=LINKED_QUESTION_SYSTEM_PROMPT,
        example_input=LINKED_QUESTION_EXAMPLE_INPUT,
        example_output=LINKED_QUESTION_EXAMPLE_OUTPUT,
    )

    _prompt = QAGenerationPrompt(
        system_prompt=DOUBLE_QUESTION_SYSTEM_PROMPT,
        example_input=DOUBLE_QUESTION_EXAMPLE_INPUT,
        example_output=DOUBLE_QUESTION_EXAMPLE_OUTPUT,
        user_input_template=DOUBLE_QUESTION_USER_TEMPLATE,
    )

    _question_type = "double"

    def generate_single_question(
        self, knowledge_base: KnowledgeBase, agent_description: str, language: str
    ) -> QuestionSample:
        seed_document = knowledge_base.get_random_document()
        context_documents = knowledge_base.get_neighbors(
            seed_document, self._context_neighbors, self._context_similarity_threshold
        )
        context_str = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])

        reference_context = "\n\n".join([f"Document {doc.id}: {doc.content}" for doc in context_documents])

        linked_questions = self._llm_complete(
            self._linked_question_generation_prompt.to_messages(
                system_prompt_input={
                    "agent_description": agent_description,
                    "language": language,
                },
                user_input=context_str,
            )
        )
        question_metadata = {
            "question_type": self._question_type,
            "original_questions": linked_questions,
            "seed_document_id": seed_document.id,
        }

        messages = self._prompt.to_messages(
            system_prompt_input={
                "language": language,
            },
            user_input={
                "question_1": linked_questions[0]["question"],
                "answer_1": linked_questions[0]["answer"],
                "question_2": linked_questions[1]["question"],
                "answer_2": linked_questions[1]["answer"],
            },
        )
        out = self._llm_complete(messages=messages)

        question = QuestionSample(
            id=str(uuid.uuid4()),
            question=out["question"],
            reference_answer=out["answer"],
            reference_context=reference_context,
            conversation_history=[],
            metadata=question_metadata,
        )

        return question


double_questions = DoubleQuestionsGenerator()
