from typing import Optional

import logging
from abc import abstractmethod
from dataclasses import dataclass, field

try:
    from tqdm.auto import tqdm
except ImportError:
    trange = range

from ..knowledge_base import KnowledgeBase
from .base_generator import BaseQuestionGenerator
from .simple_questions import SimpleQuestionGenerator

logger = logging.getLogger(__name__)


@dataclass
class BaseModifierGenerator(BaseQuestionGenerator):
    _base_generator: Optional[BaseQuestionGenerator] = field(
        default_factory=lambda: SimpleQuestionGenerator(_show_progress=False)
    )

    def _generate_single_question(self, knowledge_base: KnowledgeBase, *args) -> dict:
        return {}

    @abstractmethod
    def _modify_question(initial_question: dict, knowledge_base: KnowledgeBase, *args) -> dict:
        ...

    def _generate_questions(self, knowledge_base: KnowledgeBase, num_questions: int, *args):
        simple_questions = self._base_generator._generate_questions(knowledge_base, num_questions, *args)
        for question in tqdm(
            simple_questions, desc=f"Generating {self._question_type.name} questions", total=num_questions
        ):
            try:
                question = self._modify_question(question, knowledge_base, *args)
            except Exception as e:
                logger.error(f"Encountered error in question generation: {e}. Skipping.")
                logger.exception(e)
                continue
            yield question
