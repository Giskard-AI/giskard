from typing import Sequence

import json
import logging

import numpy as np
import pandas as pd

from ..llm.generators import BaseDataGenerator
from .prompts import (
    FIX_JSON_FORMAT_PROMPT,
    QA_GENERATION_ASSISTANT_EXAMPLE,
    QA_GENERATION_CONTEXT_EXAMPLE,
    QA_GENERATION_SYSTEM_PROMPT,
    QA_GENERATION_SYSTEM_PROMPT_MODEL,
)
from .testset import QATestset
from .vector_store import VectorStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    _qa_generation_system_prompt = QA_GENERATION_SYSTEM_PROMPT
    _qa_generation_system_prompt_model = QA_GENERATION_SYSTEM_PROMPT_MODEL
    _qa_generation_context_example = QA_GENERATION_CONTEXT_EXAMPLE
    _qa_generation_assistant_example = QA_GENERATION_ASSISTANT_EXAMPLE
    _fix_json_prompt = FIX_JSON_FORMAT_PROMPT

    _difficulty_level = 1

    def __init__(
        self,
        knowledge_df: pd.DataFrame,
        model_name: str = "",
        model_description: str = "",
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

    def _generate_question_answer_from_context(self, context):
        if self.model_name is not None or self.model_description is not None:
            system_prompt = self._qa_generation_system_prompt_model.format(
                model_name=self.model_name,
                model_description=self.model_description,
                language=self.language,
            )
        else:
            system_prompt = self._qa_generation_system_prompt.format(
                language=self.language,
            )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        if self.include_examples:
            messages.extend(
                [
                    {"role": "user", "content": self._qa_generation_context_example},
                    {"role": "assistant", "content": self._qa_generation_assistant_example},
                ]
            )
        messages.append({"role": "user", "content": context})

        return self._llm_complete(messages=messages)

    def _extract_seed_context(self):
        seed_context = self.rng.choice(self.knowledge_base.documents)
        relevant_contexts = [
            context
            for (context, score) in self.knowledge_base.similarity_search_with_score(
                [seed_context.page_content], k=self.context_neighbors
            )
            if score < self.context_similarity_threshold  # should we keep it or not ?
        ]
        return relevant_contexts

    def _format_context(self, contexts):
        context_string = "\n------\n".join(["", *[doc.page_content for doc in contexts], ""])
        return context_string

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

    def generate_dataset(self, num_samples: int = 10) -> QATestset:
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
        generated_questions = []
        for idx in range(num_samples):
            logger.info(f"Generating question {idx + 1}/{num_samples}")
            seed_contexts = self._extract_seed_context()
            context = self._format_context(seed_contexts)

            generated_qa = self._generate_question_answer_from_context(context)

            if generated_qa is not None:
                generated_questions.append(
                    {
                        "question": generated_qa["question"],
                        "reference_answer": generated_qa["answer"],
                        "reference_context": context,
                        "difficulty_level": self._difficulty_level,
                    }
                )

        return QATestset(df=pd.DataFrame(generated_questions), target=None)
