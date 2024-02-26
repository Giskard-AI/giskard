from typing import Sequence

import logging

from ..vector_store import Document
from .prompt import QAGenerationPrompt
from .question_types import QuestionTypes
from .simple_questions import SimpleQuestionGenerator

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
<description>{assistant_description}</description>
<context>{context}</context>
"""

SITUATIONAL_QUESTION_SYSTEM_PROMPT = """You are an expert at rewriting questions.
Your task is to re-write questions that will be used to evaluate the following assistant:
- Assistant description: {assistant_description}  

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


class SituationalQuestionsGenerator:
    def __init__(self, base_generator: SimpleQuestionGenerator):
        self.base_generator = base_generator

        self.situation_generation_prompt = QAGenerationPrompt(
            system_prompt=SITUATIONAL_CONTEXT_SYSTEM_PROMPT,
            user_input_template=SITUATIONAL_CONTEXT_INPUT,
        )

        self.prompt = QAGenerationPrompt(
            system_prompt=SITUATIONAL_QUESTION_SYSTEM_PROMPT,
            user_input_template=SITUATIONAL_QUESTION_USER_TEMPLATE,
        )

    def _generate_question(self, context_documents: Sequence[Document]) -> dict:
        generated_qa, question_metadata = self.base_generator._generate_question(context_documents)

        situation_generation_messages = self.situation_generation_prompt.to_messages(
            system_prompt_input={},
            user_input={
                "assistant_description": self.base_generator._assistant_description,
                "context": question_metadata["reference_context"],
            },
        )

        situational_context = "A user of the chatbot asks a general question."
        try:
            situational_context = self.base_generator._llm_client.complete(
                messages=situation_generation_messages
            ).content
        except Exception as e:
            logger.warning(
                f"Encountered error in situational context generation: {e}. Using default situational context instead."
            )

        messages = self.prompt.to_messages(
            system_prompt_input={
                "assistant_description": self.base_generator._assistant_description,
                "language": self.base_generator._language,
            },
            user_input={
                "question": generated_qa["question"],
                "answer": generated_qa["answer"],
                "situation": situational_context,
            },
        )

        out = self.base_generator._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]

        question_metadata["question_type"] = QuestionTypes.SITUATIONAL.value
        question_metadata["situational_context"] = situational_context

        return generated_qa, question_metadata
