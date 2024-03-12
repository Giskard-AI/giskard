from typing import Optional, Sequence, Union

import logging
import uuid

import pandas as pd
from tqdm.auto import tqdm

from ..llm.client import LLMClient
from .knowledge_base import KnowledgeBase
from .question_generators import BaseQuestionModifier
from .question_generators.base_question_generator import BaseQuestionsGenerator
from .testset import QATestset

logger = logging.getLogger(__name__)


def generate_testset(
    knowledge_base: KnowledgeBase,
    num_questions: int,
    question_modifiers: Optional[Union[BaseQuestionModifier, Sequence[BaseQuestionModifier]]] = None,
    base_generator: Optional[BaseQuestionsGenerator] = None,
    language: Optional[str] = None,
    assistant_description: Optional[str] = None,
    generate_simple_question: Optional[bool] = True,
    context_window_length: Optional[int] = 8192,
    llm_client: Optional[LLMClient] = None,
) -> QATestset:
    """Generate a testset from a knowledge base.
    By default it generates `num_questions` questions using the `giskard.rag.base_question_generator.BaseQuestionsGenerator`. If question modifiers are provided,
    it will generate `num_questions` questions using each of the modifiers as well.

    Parameters
    ----------
    knowledge_base : KnowledgeBase
        The knowledge base to generate questions from.
    num_questions : int
        The number of questions to generate. By default 30.
    question_modifiers : Union[BaseQuestionModifier, Sequence[BaseQuestionModifier]], optional
        Question modifiers to use for question generation. If not specified, only the base generator will be used.
        If specified it will generate questions using the base generator and each of the modifiers.
    base_generator : BaseQuestionsGenerator, optional
        The base question generator to use for question generation. If not specified, a default generator will be created.
    language: str = 'en'
        The language to use for question generation. The default is "en" to generate questions in english.
    assistant_description: str, optional
        Description of the assistant to be tested.
    generate_simple_question: bool = True
        Whether to generate simple questions with the base_generator or not. By default True.
    context_window_length: int = 8192
        Context window length of the llm used in the `llm_client` of the generator
    llm_client: LLMClient, optional
        The LLM client to use for question generation. If not specified, a default openai client will be used.

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

    question_generators = [base_generator] if generate_simple_question else []
    question_generators.extend([modifier.initialize(base_generator) for modifier in question_modifiers])

    topics = knowledge_base.topics

    generated_questions = []
    for generator in tqdm(question_generators, desc="Testset generation"):
        for idx in tqdm(range(num_questions), desc=f"Generating {generator.question_type.name} questions"):
            context_docs, topic_id = knowledge_base._get_random_document_group()
            try:
                generated_qa, question_metadata = generator.generate_question(context_docs)
                question_metadata["topic"] = topics[topic_id]
                question_metadata["seed_document_id"] = context_docs[0].id
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
