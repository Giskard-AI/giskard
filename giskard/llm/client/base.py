from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .logger import LLMLogger


@dataclass
class LLMFunctionCall:
    function: str
    args: Any


@dataclass
class LLMOutput:
    message: Optional[str] = None
    function_call: Optional[LLMFunctionCall] = None


class LLMClient(ABC):
    @property
    @abstractmethod
    def logger(self) -> LLMLogger:
        ...

    @abstractmethod
    def complete(
        self,
        messages,
        functions=None,
        model="gpt-4",
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
        caller_id: Optional[str] = None,
    ) -> LLMOutput:
        ...
