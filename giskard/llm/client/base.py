from typing import Any, Dict, Optional, Sequence

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .logger import LLMLogger


@dataclass
class LLMFunctionCall:
    function: str
    args: Any


@dataclass
class LLMToolCall:
    id: str
    function: str
    args: Any


@dataclass
class LLMOutput:
    raw_output: Any
    message: Optional[str] = None
    function_call: Optional[LLMFunctionCall] = None
    tool_calls: Sequence[LLMToolCall] = field(default_factory=list)


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
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
    ) -> LLMOutput:
        ...
