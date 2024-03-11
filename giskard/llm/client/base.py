from typing import Optional, Sequence

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .logger import LLMLogger


@dataclass
class ChatMessage:
    role: str
    content: Optional[str] = None


_logger = LLMLogger()


class LLMClient(ABC):
    @property
    def logger(self) -> LLMLogger:
        return _logger

    @abstractmethod
    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        ...
