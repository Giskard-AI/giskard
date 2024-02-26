from typing import Sequence

import logging

from ..knowledge_base import Document
from .prompt import QAGenerationPrompt
from .question_types import QuestionTypes
from .simple_questions import SimpleQuestionGenerator

logger = logging.getLogger(__name__)


LINKED_QUESTION_SYSTEM_PROMPT = """You are a powerful auditor, your role is to generate two question & answer pairs from a given list of context paragraphs.

The assistant you are auditing is the following:
- Assitant description: {assistant_description}

Your questions must be related to the provided context.  
Please respect the following rules to generate the question:
- The answers to the questions should be found inside the provided context
- Each question must be self-contained.
- Each question and answer pair must be coherent by itself and in agreement with the provided context
- The two questions and answers pairs must be about slightly different topics.
- The questions and answers must be in this language: {language}

The user will provide the context, consisting in multiple paragraphs delimited by dashes "------".
You must output a list of exactly two JSON objects with keys 'question' and 'answer'. Make sure you return a valid JSON object."""

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


class DoubleQuestionsGenerator:
    def __init__(self, base_generator: SimpleQuestionGenerator):
        self._base_generator = base_generator

        self._linked_question_generation_prompt = QAGenerationPrompt(
            system_prompt=LINKED_QUESTION_SYSTEM_PROMPT,
        )

        self._prompt = QAGenerationPrompt(
            system_prompt=DOUBLE_QUESTION_SYSTEM_PROMPT,
            user_input_template=DOUBLE_QUESTION_USER_TEMPLATE,
        )

    def _generate_question(self, context_documents: Sequence[Document]) -> dict:
        reference_context = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])
        linked_questions = self._base_generator._llm_complete(
            self._linked_question_generation_prompt.to_messages(
                system_prompt_input={
                    "assistant_description": self._base_generator._assistant_description,
                    "language": self._base_generator._language,
                },
                user_input=reference_context,
            )
        )
        question_metadata = {
            "reference_context": reference_context,
            "question_type": QuestionTypes.DOUBLE_QUESTION.value,
            "original_questions": linked_questions,
        }

        messages = self._prompt.to_messages(
            system_prompt_input={
                "language": self._base_generator._language,
            },
            user_input={
                "question_1": linked_questions[0]["question"],
                "answer_1": linked_questions[0]["answer"],
                "question_2": linked_questions[1]["question"],
                "answer_2": linked_questions[1]["answer"],
            },
        )
        out = self._base_generator._llm_complete(messages=messages)

        return out, question_metadata
