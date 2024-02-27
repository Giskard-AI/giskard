from typing import Optional, Sequence, Union

import logging
import uuid

import pandas as pd

from ..llm.client import LLMClient
from .knowledge_base import KnowledgeBase
from .question_generators import (
    ComplexQuestionsGenerator,
    ConversationalQuestionsGenerator,
    DistractingQuestionsGenerator,
    DoubleQuestionsGenerator,
    QuestionTypes,
    SimpleQuestionsGenerator,
    SituationalQuestionsGenerator,
)
from .testset import QATestset

logger = logging.getLogger(__name__)


class TestsetGenerator:
    """Testset generator for testing RAG models.

    Explore a given knowledge base and generate question/answer pairs to test the model.

    Each generated item contains the following field
    - question: a question about a part of the knowledge base
    - reference_answer: the expected answer according to the knowledge base
    - reference_context: relevant elements directly extracted from the knowledge base
    - question_type: an indicator of how difficult the question is

    Parameters
    ----------
    knowledge_base: pd.DataFrame
        A dataframe containing the whole knowledge base.
    knowledge_base_columns: Sequence[str], optional
        The list of columns from the `knowledge_base` to consider. If not specified, all columns of the knowledge base
        dataframe will be concatenated to produce a single document.
        Example: if your knowledge base consists in FAQ data with columns "Q" and "A", we will format each row into a
        single document "Q: [question]\\nA: [answer]" to generate questions.
    language: str = 'en'
        The language to use for question generation. The default is "en" to generate questions in english.
    assistant_description: str, optional
        Description of the assistant to be tested.
    context_window_length: int = 8192
        Context window length of the llm used in the `llm_client` of the generator
    llm_client: LLMClient, optional
        The LLM client to use for question generation. If not specified, a default openai client will be used.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        language: str = "en",
        assistant_description: Optional[str] = None,
        context_window_length: int = 8192,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.base_generator = SimpleQuestionsGenerator(
            knowledge_base,
            language,
            assistant_description,
            context_window_length,
            llm_client,
        )
        self.knowledge_base = knowledge_base

        self.generators = {
            QuestionTypes.EASY: self.base_generator,
            QuestionTypes.COMPLEX: ComplexQuestionsGenerator(self.base_generator),
            QuestionTypes.DISTRACTING_ELEMENT: DistractingQuestionsGenerator(self.base_generator),
            QuestionTypes.SITUATIONAL: SituationalQuestionsGenerator(self.base_generator),
            QuestionTypes.DOUBLE_QUESTION: DoubleQuestionsGenerator(self.base_generator),
            QuestionTypes.CONVERSATIONAL: ConversationalQuestionsGenerator(self.base_generator),
        }

    def generate_testset(
        self,
        num_questions: int = 10,
        question_types: Union[QuestionTypes, Sequence[QuestionTypes]] = QuestionTypes.EASY,
    ) -> QATestset:
        """Generates a testset from the knowledge base.

        Parameters
        ----------
        num_questions : int
            The number of question to generate for each question type. By default 10.
        question_types : Union[QuestionTypes, Sequence[QuestionTypes]]
            The types of the questions to generate. Can be 1 (:attr:`QuestionTypes.EASY`), 2 (:attr:`QuestionTypes.COMPLEX`),
            3 (:attr:`QuestionTypes.DISTRACTING_ELEMENT`) or a list of these values. By default will use the easy level.

        Returns
        -------
        QATestset
            The generated test set.

        """
        if not isinstance(question_types, Sequence):
            question_types = [question_types]

        generated_questions = []
        for q_type in question_types:
            for idx in range(num_questions):
                logger.info(
                    f"Generating question {idx + 1}/{num_questions} for question type {QuestionTypes(q_type).name}."
                )
                context_docs = self.knowledge_base._get_random_document_group()
                try:
                    generated_qa, question_metadata = self.generators[q_type].generate_question(context_docs)
                except Exception as e:
                    logger.error(f"Encountered error in question generation: {e}. Skipping.")
                    logger.exception(e)
                    continue

                generated_questions.append(
                    {
                        "question": generated_qa["question"],
                        "reference_answer": generated_qa["answer"],
                        "reference_context": question_metadata.pop("reference_context"),
                        "conversation_history": question_metadata.pop("conversation_history", []),
                        "id": str(uuid.uuid4()),
                        "metadata": question_metadata,
                    }
                )

        return QATestset(pd.DataFrame(generated_questions).set_index("id"))


def generate_testset(
    knowledge_base: KnowledgeBase,
    num_questions: int = 30,
    question_types: Union[QuestionTypes, Sequence[QuestionTypes]] = QuestionTypes.EASY,
    conversational: bool = False,
    **kwargs,
) -> QATestset:
    """Generate a testset from a knowledge base.

    Parameters
    ----------
    knowledge_base : KnowledgeBase
        The knowledge base to generate questions from.
    num_questions : int
        The number of questions to generate. By default 30.
    question_types : Union[QuestionTypes, Sequence[QuestionTypes]]
        The types of the questions to generate. Can be 1 (:attr:`QuestionTypes.EASY`), 2 (:attr:`QuestionTypes.COMPLEX`),
         or a list of these values. See :class:`QuestionTypes` for more question types.
    conversational : bool
        Whether to generate conversational questions or not. By default False.

    Returns
    -------
    QATestset
        The generated test set.
    """
    return TestsetGenerator(knowledge_base, **kwargs).generate_testset(
        num_questions=num_questions, question_types=question_types
    )
