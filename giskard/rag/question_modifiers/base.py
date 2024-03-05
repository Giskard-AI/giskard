from typing import Optional, Sequence, Tuple

from abc import ABC, abstractmethod

from ..base_question_generator import BaseQuestionsGenerator
from ..knowledge_base import Document


class BaseQuestionModifier(ABC):
    @abstractmethod
    def generate_question(self, context_documents: Sequence[Document]) -> Tuple[dict, dict]:
        ...

    def initialize(self, base_generator: Optional[BaseQuestionsGenerator] = None):
        self._base_generator = base_generator
        return self
