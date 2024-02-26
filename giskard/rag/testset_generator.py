from typing import Optional, Sequence, Union

import logging
import uuid

import pandas as pd

from ..llm.client import LLMClient
from .question_generators import (
    ComplexQuestionsGenerator,
    DifficultyLevel,
    DistractingQuestionsGenerator,
    SimpleQuestionGenerator,
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
    - difficulty_level: an indicator of how difficult the question is

    Parameters
    ----------
    knowledge_base: pd.DataFrame
        A dataframe containing the whole knowledge base.
    knowledge_base_columns: Sequence[str], optional
        The list of columns from the `knowledge_base` to consider. If not specified, all columns of the knowledge base
        dataframe will be concatenated to produce a single document.
        Example: if your knowledge base consists in FAQ data with columns "Q" and "A", we will format each row into a
        single document "Q: [question]\\nA: [answer]" to generate questions.
    language: str = "en"
        The language used to generate questions (e.g. "fr", "de", ...)
    assistant_description: str, optional
        Description of the assistant to be tested.
    context_neighbors: int
        The maximum number of extracted element from the knowledge base to get a relevant context for question generation
    context_similarity_threshold: float = 0.2
        A similarity threshold to filter irrelevant element from the knowledge base during context creation
    context_window_length: int = 8192
        Context window length of the llm used in the `llm_client` of the generator
    embedding_fn: Callable = None
        Embedding function to build the knowledge base index.
    seed: int = None
    """

    def __init__(
        self,
        knowledge_base: pd.DataFrame,
        knowledge_base_columns: Sequence[str] = None,
        language: str = "en",
        assistant_description: str = None,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        seed: int = None,
        include_examples: bool = True,
        embedding_model: str = "text-embedding-ada-002",
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.5,
    ) -> None:
        self.base_generator = SimpleQuestionGenerator(
            knowledge_base,
            knowledge_base_columns,
            language,
            assistant_description,
            context_neighbors,
            context_similarity_threshold,
            context_window_length,
            seed,
            include_examples,
            embedding_model,
            llm_client,
            llm_temperature,
        )

        self.generators = {
            DifficultyLevel.EASY: self.base_generator,
            DifficultyLevel.COMPLEX: ComplexQuestionsGenerator(self.base_generator),
            DifficultyLevel.DISTRACTING_ELEMENT: DistractingQuestionsGenerator(self.base_generator),
        }

    def generate_testset(
        self,
        num_questions: int = 10,
        difficulty: Union[DifficultyLevel, Sequence[DifficultyLevel]] = DifficultyLevel.EASY,
    ) -> QATestset:
        """Generates a testset from the knowledge base.

        Parameters
        ----------
        num_questions : int
            The number of question to generate for each difficulty level. By default 10.
        difficulty : Union[DifficultyLevel, Sequence[DifficultyLevel]]
            The difficulty level of the questions to generate. Can be 1 (:attr:`DifficultyLevel.EASY`), 2 (:attr:`DifficultyLevel.COMPLEX`),
            3 (:attr:`DifficultyLevel.DISTRACTING_ELEMENT`) or a list of these values. By default will use the easy level.

        Returns
        -------
        QATestset
            The generated test set.

        """
        if not isinstance(difficulty, Sequence):
            difficulty = [difficulty]

        generated_questions = []
        for level in difficulty:
            for idx in range(num_questions):
                logger.info(f"Generating question {idx + 1}/{num_questions} for difficulty level {str(level)}.")
                context_docs = self.base_generator._get_random_document_group()
                try:
                    generated_qa, question_metadata = self.generators[level]._generate_question(context_docs)
                except Exception as e:
                    logger.error(f"Encountered error in question generation: {e}. Skipping.")
                    continue

                reference_context = question_metadata["reference_context"]
                del question_metadata["reference_context"]

                generated_questions.append(
                    {
                        "question": generated_qa["question"],
                        "reference_answer": generated_qa["answer"],
                        "reference_context": reference_context,
                        "id": str(uuid.uuid4()),
                        "metadata": question_metadata,
                    }
                )

        return QATestset(pd.DataFrame(generated_questions).set_index("id"))


def generate_testset(
    knowledge_base: pd.DataFrame, num_questions: int = 30, conversational: bool = False, **kwargs
) -> QATestset:
    """Generate a testset from a knowledge base.

    Parameters
    ----------
    knowledge_base : pd.DataFrame
        The knowledge base to generate questions from.
    num_questions : int
        The number of questions to generate. By default 30.
    conversational : bool
        Whether to generate conversational questions or not. By default False.

    Returns
    -------
    QATestset
        The generated test set.
    """
    return TestsetGenerator(knowledge_base, **kwargs).generate_testset(
        num_questions=num_questions, difficulty=[1, 2, 3]
    )
