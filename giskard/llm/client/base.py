from typing import Any, Dict, List, Optional, Sequence

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel

from .logger import LLMLogger


@dataclass
class LLMFunctionCall(BaseModel):
    name: str
    arguments: Any


@dataclass
class LLMToolCall(BaseModel):
    id: str
    type: str
    function: LLMFunctionCall


@dataclass
class LLMMessage(BaseModel):
    role: str
    content: Optional[str]
    function_call: Optional[LLMFunctionCall]
    tool_calls: Optional[List[LLMToolCall]]

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
    ) -> LLMMessage:
        ...
