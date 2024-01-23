from typing import Sequence

import json

import numpy as np
import pandas as pd

from ..llm.errors import LLMGenerationError
from ..llm.generators import BaseDataGenerator
from .embeddings import EmbeddingsBase, OpenAIEmbeddings
from .prompts import (
    QA_GENERATION_ASSISTANT_EXAMPLE,
    QA_GENERATION_CONTEXT_EXAMPLE,
    QA_GENERATION_SYSTEM_PROMPT,
)
from .testset import TestSet
from .vector_store import VectorStore


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
    embedding_model: EmbeddingsBase = None
        an embedding model to build the knowledge base index
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
    _qa_generation_context_example = QA_GENERATION_CONTEXT_EXAMPLE
    _qa_generation_assistant_example = QA_GENERATION_ASSISTANT_EXAMPLE
    _one_output_requirement = "\n\nRemember you should only generate one question and answer pair."

    _difficulty_level = 1

    def __init__(
        self,
        knowledge_df: pd.DataFrame,
        model_name: str,
        model_description: str,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        embedding_model: EmbeddingsBase = None,
        language: str = "en",
        knowledge_base_features: Sequence[str] = None,
        seed: int = None,
        include_examples: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.model_description = model_description
        self.context_neighbors = context_neighbors
        self.context_similarity_threshold = context_similarity_threshold

        self.context_window_length = context_window_length
        self.embedding_model = embedding_model if embedding_model is not None else OpenAIEmbeddings()
        self.language = language
        self.rng = np.random.default_rng(seed=seed)
        self.include_examples = include_examples

        self.knowledge_base = VectorStore.from_df(knowledge_df, self.embedding_model, features=knowledge_base_features)

    def _make_generate_input_functions(self, return_attribute_name):
        return [
            {
                "name": "generate_inputs",
                "description": "generates inputs for model audit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "inputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {return_attribute_name: {"type": "string"}},
                            },
                        }
                    },
                    "required": ["inputs"],
                },
            }
        ]

    def _generate_question_answer_from_context(self, context):
        messages = [{"role": "system", "content": self._qa_generation_system_prompt}]
        if self.include_examples:
            messages.extend(
                [
                    {"role": "user", "content": self._qa_generation_context_example},
                    {"role": "assistant", "content": self._qa_generation_assistant_example},
                ]
            )
        messages.append({"role": "user", "content": context})

        generated_qa = self._llm_complete(messages=messages)
        return generated_qa["question"], generated_qa["answer"]

    def _extract_seed_context(self):
        seed_context = self.rng.choice(self.knowledge_base.documents)
        relevant_contexts = [
            context
            for (context, score) in self.knowledge_base.similarity_search_with_score(
                seed_context.page_content, k=self.context_neighbors
            )
            if score < self.context_similarity_threshold  # should we keep it or not ?
        ]
        return relevant_contexts

    def _format_context(self, contexts):
        context_string = "\n------\n".join(["", *[doc.page_content for doc in contexts], ""])
        context_string = context_string + self._one_output_requirement
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
        except (AttributeError, KeyError) as err:
            raise LLMGenerationError("Could not parse generated inputs") from err
        except json.decoder.JSONDecodeError as err:
            if "Extra data:" in str(err):
                raise LLMGenerationError("Generator model output more than one question/answer pair.") from err
            else:
                raise err

        return generated

    def generate_dataset(self, num_samples: int = 10) -> TestSet:
        """Generates a testset from the knowledge base.

        Parameters
        ----------
        num_samples : int
            The number of question to generate, by default 10.

        Returns
        -------
        TestSet
            The generated test set.

        Each generated question has the following field:
        - question: a question about a part of the knowledge base
        - reference_answer: the expected answer according to the knowledge base
        - reference_context: relevant elements directly extracted from the knowledge base
        - difficulty_level: an indicator of how difficult the question is
        """
        generated_questions = []
        for idx in range(num_samples):
            seed_contexts = self._extract_seed_context()
            context = self._format_context(seed_contexts)

            question, answer = self._generate_question_answer_from_context(context)

            generated_questions.append(
                {
                    "question": question,
                    "reference_answer": answer,
                    "reference_context": context,
                    "difficulty_level": self._difficulty_level,
                }
            )

        return TestSet(df=pd.DataFrame(generated_questions))
