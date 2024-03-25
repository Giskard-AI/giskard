from typing import Dict, Iterator, Optional, Sequence

import json
import logging
import re
from abc import ABC, abstractmethod

from ...llm.client import LLMClient, LLMMessage, get_default_client
from ..knowledge_base import KnowledgeBase

logger = logging.getLogger("giskard.rag")


class QuestionGenerator(ABC):
    @abstractmethod
    def generate_questions(self, knowledge_base: KnowledgeBase, num_questions: int, *args, **kwargs) -> Iterator[int]:
        ...


class _LLMBasedQuestionGenerator(QuestionGenerator):
    def __init__(
        self,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        context_window_length: int = 8192,
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.4,
    ):
        self._context_window_length = context_window_length
        self._context_neighbors = context_neighbors
        self._context_similarity_threshold = context_similarity_threshold
        self._llm_client_instance = llm_client
        self._llm_temperature = llm_temperature

    @property
    def _llm_client(self):
        if self._llm_client_instance is None:
            return get_default_client()

        return self._llm_client_instance

    def _llm_complete(self, messages: Sequence[LLMMessage]) -> dict:
        out = self._llm_client.complete(
            messages=messages,
            temperature=0.5,
            caller_id=self.__class__.__name__,
        )

        return self._parse_json_output(out.content)

    def _parse_json_output(self, raw_json: str):
        try:
            return json.loads(raw_json, strict=False)
        except json.JSONDecodeError:
            logger.debug("JSON decoding error, trying to fix the JSON string.")

        logger.debug("Raw output: %s", raw_json)
        # Let's see if it's just a matter of markdown format (```json ... ```)
        match = re.search(r"```json\s{0,5}(.*?)\s{0,5}```", raw_json, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1), strict=False)
            except json.JSONDecodeError:
                pass

        # Final attempt, let's try to fix the JSON with the LLM itself
        out = self._llm_client.complete(
            messages=[
                LLMMessage(
                    role="system",
                    content="Fix the following text so it contains a single valid JSON object. Make sure to start and end with curly brackets.",
                ),
                LLMMessage(role="user", content=raw_json),
            ],
            temperature=0,
            caller_id=self.__class__.__name__,
        )
        return json.loads(out.content, strict=False)


class GenerateFromSingleQuestionMixin:
    _question_type: str

    def generate_questions(self, knowledge_base: KnowledgeBase, num_questions: int, *args, **kwargs) -> Iterator[Dict]:
        for _ in range(num_questions):
            try:
                yield self.generate_single_question(knowledge_base, *args, **kwargs)
            except Exception as e:  # @TODO: specify exceptions
                logger.error(f"Encountered error in question generation: {e}. Skipping.")
                logger.exception(e)


class _BaseModifierGenerator(_LLMBasedQuestionGenerator):
    _base_generator: QuestionGenerator
    _question_type: str

    @abstractmethod
    def _modify_question(initial_question: dict, knowledge_base: KnowledgeBase, *args, **kwargs) -> Dict:
        ...

    def generate_questions(self, knowledge_base: KnowledgeBase, num_questions: int, *args, **kwargs) -> Iterator[Dict]:
        # Generate the base questions
        base_questions = self._base_generator.generate_questions(knowledge_base, num_questions, *args, **kwargs)

        # Run the modifier for each
        for question in base_questions:
            try:
                yield self._modify_question(question, knowledge_base, *args, **kwargs)
            except Exception as e:  # @TODO: specify exceptions
                logger.error(f"Encountered error in question generation: {e}. Skipping.")
                logger.exception(e)
