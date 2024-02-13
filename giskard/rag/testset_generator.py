from typing import Optional, Sequence, Union

import json
import logging
from enum import Enum

import numpy as np
import pandas as pd

from ..llm.client import get_default_client
from ..llm.client.base import LLMClient
from .prompts import (
    FIX_JSON_FORMAT_PROMPT,
    DistractingQuestionPrompt,
    QAGenerationPrompt,
    QuestionComplexificationPrompt,
)
from .testset import QATestset
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class DifficultyLevel(int, Enum):
    EASY = 1
    COMPLEX = 2
    DISTRACTING_ELEMENT = 3


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
    model_name: str, optional
        Name of the model to be tested, to get more fitting questions.
    model_description: str, optional
        Description of the model to be tested.
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
        model_name: str = None,
        model_description: str = None,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        seed: int = None,
        include_examples: bool = True,
        embedding_model: str = "text-embedding-ada-002",
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.5,
    ):
        self._knowledge_base = knowledge_base
        self._knowledge_base_columns = knowledge_base_columns
        self._language = language
        self._model_name = model_name
        self._model_description = model_description
        self._context_neighbors = context_neighbors
        self._context_similarity_threshold = context_similarity_threshold
        self._embedding_model = embedding_model
        self._context_window_length = context_window_length
        self._rng = np.random.default_rng(seed=seed)
        self._include_examples = include_examples
        self._vector_store_inst = None
        self._llm_client = llm_client or get_default_client()
        self._llm_temperature = llm_temperature

    @property
    def _vector_store(self):
        if self._vector_store_inst is None:
            logger.debug("Initializing vector store from knowledge base.")
            self._vector_store_inst = VectorStore.from_df(
                self._knowledge_base,
                lambda query: self._llm_client.embeddings(query, model=self._embedding_model),
                features=self._knowledge_base_columns,
            )
        return self._vector_store_inst

    def _get_generator_method(self, level: DifficultyLevel):
        mapping = {
            DifficultyLevel.EASY: self._generate_question_easy,
            DifficultyLevel.COMPLEX: self._generate_question_complex,
            DifficultyLevel.DISTRACTING_ELEMENT: self._generate_question_distracting_element,
        }

        try:
            return mapping[level]
        except KeyError:
            raise ValueError(f"Invalid difficulty level: {level}.")

    def _generate_question_easy(self, context: str) -> dict:
        messages = QAGenerationPrompt.create_messages(
            model_name=self._model_name,
            model_description=self._model_description,
            language=self._language,
            user_content=context,
        )

        generated_qa = self._llm_complete(messages=messages)
        generated_qa["difficulty"] = DifficultyLevel.EASY
        return generated_qa

    def _generate_question_complex(self, context: str) -> dict:
        generated_qa = self._generate_question_easy(context)

        messages = QuestionComplexificationPrompt.create_messages(
            model_name=self._model_name,
            model_description=self._model_description,
            language=self._language,
            user_content=(generated_qa["question"], context),
        )
        generated_qa["difficulty"] = DifficultyLevel.COMPLEX
        out = self._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]
        return generated_qa

    def _generate_question_distracting_element(self, context: str) -> dict:
        generated_qa = self._generate_question_easy(context)

        distracting_context = self._rng.choice(self._vector_store.documents).content
        messages = DistractingQuestionPrompt.create_messages(
            model_name=self._model_name,
            model_description=self._model_description,
            language=self._language,
            user_content=(generated_qa["question"], generated_qa["answer"], distracting_context),
        )
        generated_qa["difficulty"] = DifficultyLevel.DISTRACTING_ELEMENT
        out = self._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]
        return generated_qa

    def _get_random_document_group(self):
        seed_embedding = self._rng.choice(self._vector_store.embeddings)
        relevant_contexts = [
            context
            for (context, score) in self._vector_store.vector_similarity_search_with_score(
                seed_embedding, k=self._context_neighbors
            )
            if score < self._context_similarity_threshold
        ]

        return relevant_contexts

    def _prevent_context_window_overflow(self, prompt: str):
        # Prevent context overflow
        # general rule of thumbs to count tokens: 1 token ~ 4 characters
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        return prompt[: self._context_window_length * 4]

    def _llm_complete(self, messages: Sequence[dict]) -> dict:
        try:
            out = self._llm_client.complete(
                messages=messages,
                temperature=self._llm_temperature,
                caller_id=self.__class__.__name__,
            )

            return json.loads(out.content, strict=False)
        except json.decoder.JSONDecodeError:
            logger.warning("JSON decoding error, trying to fix the JSON string.")
            return self._try_fix_json_message(out.content)

    def _try_fix_json_message(self, incorrect_json: str):
        out = self._llm_client.complete(
            messages=[
                {"role": "system", "content": FIX_JSON_FORMAT_PROMPT},
                {"role": "user", "content": incorrect_json},
            ],
            temperature=0,
            caller_id=self.__class__.__name__,
        )
        return json.loads(out.content)

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
                context_docs = self._get_random_document_group()
                context = QAGenerationPrompt.format_context(context_docs)

                generation_fn = self._get_generator_method(level)

                try:
                    generated_qa = generation_fn(context)
                except Exception as e:
                    logger.error(f"Encountered error in question generation: {e}. Skipping.")
                    continue

                generated_questions.append(
                    {
                        "question": generated_qa["question"],
                        "reference_answer": generated_qa["answer"],
                        "reference_context": context,
                        "difficulty_level": generated_qa["difficulty"],
                    }
                )

        return QATestset(pd.DataFrame(generated_questions))
