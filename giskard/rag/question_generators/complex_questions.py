from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import _BaseModifierGenerator
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionsGenerator

COMPLEXIFICATION_SYSTEM_PROMPT = """You are an expert at writing questions. 
Your task is to re-write questions that will be used to evaluate the following agent:
- Model description: {agent_description}  

Respect the following rules to reformulate the question:
- The re-written question should not be longer than the original question by up to 10 to 15 words. 
- The re-written question should be more elaborated than the original, use elements from the context to enrich the questions. 
- The re-written question should be more difficult to handle for AI models but it must be understood and answerable by humans.
- Add one or more constraints / conditions to the question.
- The re-written question must be in this language: {language}

You will be provided the question delimited by <question></question> tags.
You will also be provided a relevant context which contain the answer to the question, delimited by <context></context> tags. It consists in multiple paragraphs delimited by dashes "------".
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

COMPLEXIFICATION_INPUT_TEMPLATE = """<question>
{question}
</question>

<context>
{context}
</context>
"""

COMPLEXIFICATION_EXAMPLE_INPUT = """<question>
For which countries can I track my shipping?
</question>

<context>
What payment methods do you accept?

\tWe accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
<context>
"""

COMPLEXIFICATION_EXAMPLE_OUTPUT = """{
    "question": "Can you provide my a list of the countries from which I can follow the advancement of the delivery of my shipping?"
}"""


class ComplexQuestionsGenerator(_BaseModifierGenerator):
    """
    Complex question generator that generates questions from a KnowledgeBase.
    This generator is a subclass of the `_BaseModifierGenerator` class. Hence it has a `_base_generator` attribute that is an instance of the `SimpleQuestionsGenerator` class.

    Generates first simple question that will be complexified.

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

    _base_generator = SimpleQuestionsGenerator()

    _prompt = QAGenerationPrompt(
        system_prompt=COMPLEXIFICATION_SYSTEM_PROMPT,
        example_input=COMPLEXIFICATION_EXAMPLE_INPUT,
        example_output=COMPLEXIFICATION_EXAMPLE_OUTPUT,
        user_input_template=COMPLEXIFICATION_INPUT_TEMPLATE,
    )

    _question_type = "complex"

    def _modify_question(
        self, question: QuestionSample, knowledge_base: KnowledgeBase, agent_description: str, language: str
    ) -> QuestionSample:
        """
        Modify a question by complexifying it.

        Parameters
        ----------
        question : QuestionSample
            The question to modify.
        knowledge_base : KnowledgeBase
            The knowledge base to use for question generation.
        agent_description : str
            The description of the agent.
        language : str
            The language to use for question generation.

        Returns
        -------
        QuestionSample
            The modified question.
        """
        messages = self._prompt.to_messages(
            system_prompt_input={
                "agent_description": agent_description,
                "language": language,
            },
            user_input={"question": question.question, "context": question.reference_context},
        )
        question.metadata["question_type"] = self._question_type
        out = self._llm_complete(messages=messages)
        question.question = out["question"]
        return question


complex_questions = ComplexQuestionsGenerator()
