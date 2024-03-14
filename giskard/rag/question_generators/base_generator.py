from typing import Optional, Sequence

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

try:
    from tqdm.auto import trange
except ImportError:
    trange = range

from ...llm.client import LLMClient, LLMMessage, get_default_client
from ..knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


@dataclass
class BaseQuestionGenerator(ABC):
    _context_window_length: Optional[int] = 8192
    _llm_client: Optional[LLMClient] = field(default_factory=get_default_client)
    _llm_temperature: Optional[float] = 0.5
    _context_neighbors: Optional[int] = 4
    _context_similarity_threshold: Optional[float] = 0.2
    _show_progress: Optional[bool] = True

    @abstractmethod
    def _generate_single_question(self, knowledge_base: KnowledgeBase, *args) -> dict:
        ...

    def _generate_questions(self, knowledge_base: KnowledgeBase, num_questions: int, *args):
        for _ in trange(
            num_questions, desc=f"Generating {self._question_type.name} questions", disable=not self._show_progress
        ):
            try:
                question = self._generate_single_question(knowledge_base, *args)
            except Exception as e:
                logger.error(f"Encountered error in question generation: {e}. Skipping.")
                logger.exception(e)
                continue
            yield question

    def _llm_complete(self, messages: Sequence[LLMMessage]) -> dict:
        try:
            out = self._llm_client.complete(
                messages=messages,
                temperature=0.5,
                caller_id=self.__class__.__name__,
            )

            return json.loads(out.content, strict=False)
        except json.decoder.JSONDecodeError:
            print(out)
            logger.warning("JSON decoding error, trying to fix the JSON string.")
            return self._try_fix_json_message(out.content)

    def _try_fix_json_message(self, incorrect_json: str):
        out = self._llm_client.complete(
            messages=[
                LLMMessage(
                    role="system",
                    content="Fix the following json string so it contains a single valid json. Make sure to start and end with curly brackets.",
                ),
                LLMMessage(role="user", content=incorrect_json),
            ],
            temperature=0,
            caller_id=self.__class__.__name__,
        )
        return json.loads(out.content)
