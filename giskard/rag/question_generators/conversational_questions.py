from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import _BaseModifierGenerator
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionsGenerator

CONVERSATIONAL_SYSTEM_PROMPT = """You are an expert at re-writing questions.

Your task is to split a question into two messages. First, the introduction message present the request of the user, and then the second message ask the question without any reference to the topic.

Please respect the following rules to generate the question:
- The introduction message should not ask the question.
- The introduction message MUST contain all the objects and complements from the original question.
- The second message should ask a question without any reference to the topic or context.
- The second message should use demonstrative pronouns or other indirect references as much as possible.
- The second message should not understandable without the first message, it should NOT be self-contained.
- The messages and answer must be in this language: {language}.
- Make sure that the meaning of the original question cannot be inferred from the generated question.

You will be provided the original question between <question> and </question> tags.
Your output should be a single JSON object, with keys 'introduction' and 'question'. Make sure you return a valid JSON object.
"""
CONVERSATIONAL_USER_TEMPLATE = "<question>{question}</question>"
CONVERSATIONAL_USER_EXAMPLE = CONVERSATIONAL_USER_TEMPLATE.format(
    question="Is it possible to repair the car without any tools?"
)

CONVERSATIONAL_AGENT_EXAMPLE = (
    """{"introduction":"I want to repair the car without tools.","question":"Is it possible?"}"""
)


class ConversationalQuestionsGenerator(_BaseModifierGenerator):
    _base_generator = SimpleQuestionsGenerator()

    _prompt = QAGenerationPrompt(
        system_prompt=CONVERSATIONAL_SYSTEM_PROMPT,
        example_input=CONVERSATIONAL_USER_EXAMPLE,
        example_output=CONVERSATIONAL_AGENT_EXAMPLE,
        user_input_template=CONVERSATIONAL_USER_TEMPLATE,
    )

    _question_type = "conversational"

    def _modify_question(
        self, question: QuestionSample, knowledge_base: KnowledgeBase, agent_description: str, language: str
    ) -> QuestionSample:
        messages = self._prompt.to_messages(
            system_prompt_input={
                "language": language,
            },
            user_input={
                "question": question.question,
            },
        )

        out = self._llm_complete(messages=messages)
        question.question = out["question"]

        question.metadata["question_type"] = self._question_type
        question.conversation_history = [
            {"role": "user", "content": out["introduction"]},
            {"role": "assistant", "content": "How can I help you with that?"},
        ]

        return question


conversational_questions = ConversationalQuestionsGenerator()
