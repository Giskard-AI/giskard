from typing import Sequence

import numpy as np
import pandas as pd

from ..datasets import Dataset
from ..llm.errors import LLMGenerationError
from ..llm.generators import BaseDataGenerator
from .embeddings import EmbeddingsBase, OpenAIEmbeddings
from .prompts import ANSWER_GENERATION_PROMPT, QUESTION_GENERATION_PROMPT
from .vector_store import VectorStore


class KnowledgeBaseTestsetGenerator(BaseDataGenerator):
    _question_generation_prompt = QUESTION_GENERATION_PROMPT
    _answer_generation_prompt = ANSWER_GENERATION_PROMPT
    _difficulty_level = 1

    def __init__(
        self,
        knowledge_df,
        model_name: str,
        model_description: str,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        embedding_model: EmbeddingsBase = None,
        language: str = "english",
        knowledge_base_features: Sequence[str] = None,
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

    def _generate_question_from_context(self, context):
        prompt = self._question_generation_prompt.format(
            context=context,
            model_name=self.model_name,
            model_description=self.model_description,
            language=self.language,
        )
        prompt = self._prevent_context_window_overflow(prompt)
        return self._llm_complete(prompt, self._make_generate_input_functions("question"))

    def _generate_answer_from_context(self, question, context):
        prompt = self._answer_generation_prompt.format(question=question, context=context)
        prompt = self._prevent_context_window_overflow(prompt)
        return self._llm_complete(prompt, self._make_generate_input_functions("answer"))

    def _extract_seed_context(self):
        seed_context = np.random.choice(self.knowledge_base.documents)
        relevant_contexts = [
            context
            for (context, score) in self.knowledge_base.similarity_search_with_score(
                seed_context.page_content, k=self.context_neighbors
            )
            if score < self.context_similarity_threshold  # should we keep it or not ?
        ]
        return relevant_contexts

    def _format_context(self, contexts):
        context_string = "\n\n".join(
            ["### Context {} ###\n{}\n######".format(idx + 1, c.page_content) for idx, c in enumerate(contexts)]
        )
        return context_string

    def _prevent_context_window_overflow(self, prompt):
        # Prevent context overflow
        # general rule of thumbs to count tokens: 1 token ~ 4 characters
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        return prompt[: self.context_window_length * 4]

    def _llm_complete(self, prompt, functions):
        try:
            out = self.llm_client.complete(
                messages=[{"role": "system", "content": prompt}],
                functions=functions,
                function_call={"name": "generate_inputs"},
                temperature=self.llm_temperature,
                caller_id=self.__class__.__name__,
            )
            generated = out.function_call.args["inputs"]
        except (AttributeError, KeyError) as err:
            raise LLMGenerationError("Could not parse generated inputs") from err

        return generated

    def generate_dataset(self, num_samples: int = 10) -> Dataset:
        generated_questions = []
        for idx in range(num_samples):
            seed_contexts = self._extract_seed_context()
            context = self._format_context(seed_contexts)

            question = self._generate_question_from_context(context)[0]
            answer = self._generate_answer_from_context(question["question"], context)[0]

            generated_questions.append(
                {
                    "question": question["question"],
                    "reference_answer": answer["answer"],
                    "reference_context": context,
                    "difficulty_level": self._difficulty_level,
                }
            )

        return pd.DataFrame(generated_questions)
