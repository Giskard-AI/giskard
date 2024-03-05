from typing import Optional, Sequence, Union

import logging
import uuid

import pandas as pd

from ..llm.client import LLMClient
from .base_question_generator import BaseQuestionsGenerator
from .knowledge_base import KnowledgeBase
from .question_modifiers import BaseQuestionModifier
from .testset import QATestset

logger = logging.getLogger(__name__)


def generate_testset(
    knowledge_base: KnowledgeBase,
    num_questions: int = 30,
    base_generator: Optional[BaseQuestionsGenerator] = None,
    question_modifiers: Optional[Union[BaseQuestionModifier, Sequence[BaseQuestionModifier]]] = None,
    language: str = "en",
    assistant_description: Optional[str] = None,
    context_window_length: int = 8192,
    llm_client: Optional[LLMClient] = None,
    conversational: bool = False,
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
    language: str = 'en'
        The language to use for question generation. The default is "en" to generate questions in english.
    assistant_description: str, optional
        Description of the assistant to be tested.
    context_window_length: int = 8192
        Context window length of the llm used in the `llm_client` of the generator
    llm_client: LLMClient, optional
        The LLM client to use for question generation. If not specified, a default openai client will be used.
    conversational : bool
        Whether to generate conversational questions or not. By default False.

    Returns
    -------
    QATestset
        The generated test set.
    """

    if base_generator is None:
        base_generator = BaseQuestionsGenerator(
            knowledge_base, language, assistant_description, context_window_length, llm_client
        )

    question_modifiers = question_modifiers or []
    if not isinstance(question_modifiers, Sequence):
        question_modifiers = [question_modifiers]

    question_generators = [base_generator] + [modifier.initialize(base_generator) for modifier in question_modifiers]

    topics = knowledge_base.topics

    generated_questions = []
    for generator in question_generators:
        for idx in range(num_questions):
            logger.info(
                f"Generating question {idx + 1}/{num_questions} for question type {generator.question_type.name}."
            )
            context_docs, topic_id = knowledge_base._get_random_document_group()
            try:
                generated_qa, question_metadata = generator.generate_question(context_docs)
                question_metadata["topic"] = topics[topic_id]
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
            except Exception as e:
                logger.error(f"Encountered error in question generation: {e}. Skipping.")
                logger.exception(e)
                continue

    return QATestset(pd.DataFrame(generated_questions).set_index("id"))
