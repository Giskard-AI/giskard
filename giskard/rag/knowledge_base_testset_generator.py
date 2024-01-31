from typing import Sequence

import json
import logging
from enum import Enum

import numpy as np
import pandas as pd

from ..llm.generators import BaseDataGenerator
from .prompts import (
    FIX_JSON_FORMAT_PROMPT,
    DistractingQuestionPrompt,
    QAGenerationPrompt,
    QuestionComplexificationPrompt,
)
from .testset import QATestset
from .vector_store import VectorStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DifficultyLevel(int, Enum):
    DIFF_1 = 1
    DIFF_2 = 2
    DIFF_3 = 3


class KnowledgeBaseTestsetGenerator(BaseDataGenerator):
    """Testset generator for testing RAG models.

    Explore a given knowledge base and generate question/answer pairs to test the model.

    Each generated item contains the following field
    - question: a question about a part of the knowledge base
    - reference_answer: the expected answer according to the knowledge base
    - reference_context: relevant elements directly extracted from the knowledge base
    - difficulty_level: an indicator of how difficult the question is

    Parameters
    ----------
    knowledge_df: pd.DataFrame
        a dataframe containing the whole knowledge base
    model_name: str
        name of the model to be tested
    model_description: str
        a description of the model to be tested, to get more fitting questions
    context_neighbors: int
        the maximum number of extracted element from the knowledge base to get a relevant context for question generation
    context_similarity_threshold: float = 0.2
        a similarity threshold to filter irrelevant element from the knowledge base during context creation
    context_window_length: int = 8192
        context window length of the llm used in the `llm_client` of the generator
    embedding_fn: Callable = None
        an embedding function to build the knowledge base index
    language: str = "en"
        the language in which question are generated (following ISO 639-1)
    knowledge_base_features: Sequence[str] = None
        a list of columns from the `knowledge_df` to include inside the knowledge base. If the
        `knowledge_df` only has one column, it will be used by default has the content of
        the knowledge base elements. If `knowledge_df` has multiple columns they will be
        concatenated into a single column with the name of the column before the respective content.
        If `knowledge_base_features` is specified, only the columns from it are considered.

        Example: "col_1: content column 1, col_2: content column 2"
    seed: int = None
    """

    # _qa_generation_system_prompt = QA_GENERATION_SYSTEM_PROMPT
    # _qa_generation_system_prompt_model = QA_GENERATION_SYSTEM_PROMPT_MODEL
    # _qa_generation_context_example = QA_GENERATION_CONTEXT_EXAMPLE
    # _qa_generation_assistant_example = QA_GENERATION_ASSISTANT_EXAMPLE
    _fix_json_prompt = FIX_JSON_FORMAT_PROMPT

    def __init__(
        self,
        knowledge_df: pd.DataFrame,
        model_name: str = None,
        model_description: str = None,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        language: str = "en",
        knowledge_base_features: Sequence[str] = None,
        seed: int = None,
        include_examples: bool = True,
        embedding_model: str = "text-embedding-ada-002",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.model_description = model_description
        self.context_neighbors = context_neighbors
        self.context_similarity_threshold = context_similarity_threshold
        self.embedding_model = embedding_model
        self.context_window_length = context_window_length
        self.language = language
        self.rng = np.random.default_rng(seed=seed)
        self.include_examples = include_examples

        self.knowledge_base = VectorStore.from_df(
            knowledge_df,
            lambda query: self.llm_client.embeddings(query, model=self.embedding_model),
            features=knowledge_base_features,
        )

    def _difficulty_level_mapping(self, level: DifficultyLevel):
        match level:
            case DifficultyLevel.DIFF_1:
                return self._generate_question_answer_from_context
            case DifficultyLevel.DIFF_2:
                return self._generate_complex_questions_from_context
            case DifficultyLevel.DIFF_3:
                return self._generate_distraction_questions_from_context
            case _:
                raise NotImplementedError(f"Missing case for difficulty level {level}.")

    def _generate_question_answer_from_context(self, context):
        messages = QAGenerationPrompt.create_messages(
            model_name=self.model_name,
            model_description=self.model_description,
            language=self.language,
            user_content=context,
        )

        generated_qa = self._llm_complete(messages=messages)
        generated_qa["difficulty"] = DifficultyLevel.DIFF_1
        return generated_qa

    def _generate_complex_questions_from_context(self, context):
        generated_qa = self._generate_question_answer_from_context(context)

        messages = QuestionComplexificationPrompt.create_messages(
            model_name=self.model_name,
            model_description=self.model_description,
            language=self.language,
            user_content=(generated_qa["question"], context),
        )
        generated_qa["difficulty"] = DifficultyLevel.DIFF_2
        out = self._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]
        return generated_qa

    def _generate_distraction_questions_from_context(self, context):
        generated_qa = self._generate_question_answer_from_context(context)

        distracting_context = self.rng.choice(self.knowledge_base.documents).page_content
        messages = DistractingQuestionPrompt.create_messages(
            model_name=self.model_name,
            model_description=self.model_description,
            language=self.language,
            user_content=(generated_qa["question"], generated_qa["answer"], distracting_context),
        )
        generated_qa["difficulty"] = DifficultyLevel.DIFF_3
        out = self._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]
        return generated_qa

    def _extract_seed_context(self):
        seed_embedding = self.rng.choice(self.knowledge_base.embeddings)
        relevant_contexts = [
            context
            for (context, score) in self.knowledge_base.vector_similarity_search_with_score(
                seed_embedding[None], k=self.context_neighbors
            )
            if score < self.context_similarity_threshold  # should we keep it or not ?
        ]
        return relevant_contexts

    def _prevent_context_window_overflow(self, prompt):
        # Prevent context overflow
        # general rule of thumbs to count tokens: 1 token ~ 4 characters
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        return prompt[: self.context_window_length * 4]

    def _llm_complete(self, messages):
        try:
            out = self.llm_client.complete(
                messages=messages,
                temperature=self.llm_temperature,
                caller_id=self.__class__.__name__,
            )

            generated = json.loads(out.message, strict=False)
        except json.decoder.JSONDecodeError:
            logger.warning("JSON decoding error, trying to fix the JSON string.")
            generated = self._try_fix_json_message(out.message)
        return generated

    def _try_fix_json_message(self, incorrect_json):
        try:
            out = self.llm_client.complete(
                messages=[
                    {"role": "system", "content": self._fix_json_prompt},
                    {"role": "user", "content": incorrect_json},
                ],
                temperature=0,
                caller_id=self.__class__.__name__,
            )
            corrected_message = json.loads(out.message)
        except Exception:
            logger.warning("Fixing JSON format failed, question generation skipped.")
            return None
        return corrected_message

    def generate_dataset(self, num_samples: int = 10, difficulty_levels: Sequence[DifficultyLevel] = None) -> QATestset:
        """Generates a testset from the knowledge base.

        Parameters
        ----------
        num_samples : int
            The number of question to generate, by default 10.

        Returns
        -------
        QATestset
            The generated test set.
            Each generated question has the following field:
                - *question*: a question about a part of the knowledge base
                - *reference_answer*: the expected answer according to the knowledge base
                - *reference_context*: relevant elements directly extracted from the knowledge base
                - *difficulty_level*: an indicator of how difficult the question is

        """
        difficulty_levels = difficulty_levels or [DifficultyLevel.DIFF_1]
        generated_questions = []
        for level in difficulty_levels:
            for idx in range(num_samples):
                logger.info(f"Generating question {idx + 1}/{num_samples} for difficulty level {str(level.value)}.")
                seed_contexts = self._extract_seed_context()
                context = QAGenerationPrompt.format_context(seed_contexts)

                generation_fn = self._difficulty_level_mapping(level)
                generated_qa = generation_fn(context)

                if generated_qa is not None:
                    generated_questions.append(
                        {
                            "question": generated_qa["question"],
                            "reference_answer": generated_qa["answer"],
                            "reference_context": context,
                            "difficulty_level": generated_qa["difficulty"],
                        }
                    )
                else:
                    logger.warning("Error in question generation, skipping it.")

        return QATestset(df=pd.DataFrame(generated_questions), target=None)
