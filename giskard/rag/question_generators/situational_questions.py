import logging

from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import _BaseModifierGenerator
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionsGenerator

logger = logging.getLogger(__name__)


SITUATIONAL_CONTEXT_SYSTEM_PROMPT = """You are a creative writer and you goal is to write short situational description of a user using the chatbot and its intentions.
Your description must be 1 sentence long. 
You will be given the chatbot description delimited by XML tags. 
You will also be provided with a context paragraph delimited with <context></context> tags.

The situational description must be plausible given the context and the chatbot description. 
Do not mention that the user is using a chatbot or any thing related to the chatbot description.
If not enough information is provided inside the context use only the chatbot description to generate the situational context.
Be creative and imaginative.

You must only return one the situational description, nothing else.
"""

SITUATIONAL_CONTEXT_INPUT = """
<description>{agent_description}</description>
<context>{context}</context>
"""

SITUATIONAL_QUESTION_SYSTEM_PROMPT = """You are an expert at rewriting questions.
Your task is to re-write questions that will be used to evaluate the following agent:
- Agent description: {agent_description}  

Your task is to add situational context about the user inside the question. 
Please respect the following rules to generate the question:
- The question must include the information from the situational context.
- The question must sound plausible and coming from a real human user.
- The question can start with any form of greetings or not, choose randomly
- The original question and answer should be preserved.
- The question must be self-contained and understandable by humans. 
- The question must be in this language: {language}.

You will be provided the question and answer delimited with XML tags.
You will also be provided a situational context delimited with <situation></situation> tags.
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

SITUATIONAL_QUESTION_USER_TEMPLATE = """<question>
{question}
</question>
<answer>
{answer}
</answer>
<situation>
{situation}
</situation>"""

SITUATIONAL_QUESTION_EXAMPLE_INPUT = SITUATIONAL_QUESTION_USER_TEMPLATE.format(
    question="How many people are in France?",
    answer="There are nearly 70M people living in France",
    situation="A student from Canada is going to study in Europe.",
)

SITUATIONAL_QUESTION_EXAMPLE_OUTPUT = (
    """{"question": "I am a student from Canada and I am going to study in Europe. How many people are in France?"}"""
)


class SituationalQuestionsGenerator(_BaseModifierGenerator):
    _base_generator = SimpleQuestionsGenerator()

    _situation_generation_prompt = QAGenerationPrompt(
        system_prompt=SITUATIONAL_CONTEXT_SYSTEM_PROMPT,
        user_input_template=SITUATIONAL_CONTEXT_INPUT,
        example_input=SITUATIONAL_QUESTION_EXAMPLE_INPUT,
        example_output=SITUATIONAL_QUESTION_EXAMPLE_OUTPUT,
    )

    _prompt = QAGenerationPrompt(
        system_prompt=SITUATIONAL_QUESTION_SYSTEM_PROMPT,
        user_input_template=SITUATIONAL_QUESTION_USER_TEMPLATE,
    )

    _question_type = "situational"

    def _modify_question(
        self, question: QuestionSample, knowledge_base: KnowledgeBase, agent_description: str, language: str
    ) -> QuestionSample:
        situation_generation_messages = self._situation_generation_prompt.to_messages(
            system_prompt_input={},
            user_input={
                "agent_description": agent_description,
                "context": question.reference_context,
            },
        )

        situational_context = "A user of the chatbot asks a general question."
        try:
            situational_context = self._llm_client.complete(messages=situation_generation_messages).content
        except Exception as e:
            logger.warning(
                f"Encountered error in situational context generation: {e}. Using default situational context instead."
            )

        messages = self._prompt.to_messages(
            system_prompt_input={
                "agent_description": agent_description,
                "language": language,
            },
            user_input={
                "question": question.question,
                "answer": question.reference_answer,
                "situation": situational_context,
            },
        )

        out = self._llm_complete(messages=messages)
        question.question = out["question"]

        question.metadata["question_type"] = self._question_type
        question.metadata["situational_context"] = situational_context

        return question


situational_questions = SituationalQuestionsGenerator()
