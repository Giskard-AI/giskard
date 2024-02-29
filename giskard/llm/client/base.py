from typing import Any, Dict, List, Optional, Sequence

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from .logger import LLMLogger


@dataclass
class LLMFunctionCall:
    name: str
    arguments: Any


@dataclass
class LLMToolCall:
    id: str
    type: str
    function: LLMFunctionCall


@dataclass
class LLMMessage:
    role: str
    content: Optional[str] = None
    function_call: Optional[LLMFunctionCall] = None
    tool_calls: Optional[List[LLMToolCall]] = None

    @staticmethod
    def create_message(role: str, content: str):
        return LLMMessage(role=role, content=content, function_call=None, tool_calls=None)


class LLMClient(ABC):
    @property
    @abstractmethod
    def logger(self) -> LLMLogger:
        ...

    @abstractmethod
    def complete(
        self,
        messages: Sequence[LLMMessage],
        functions=None,
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
        seed: Optional[int] = None,
    ) -> LLMMessage:
        ...

    @abstractmethod
    def embeddings(self, text) -> np.ndarray:
        ...
