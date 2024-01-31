from typing import Any, Dict, List, Optional, Sequence

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .logger import LLMLogger


@dataclass
class LLMFunctionCall:
    name: str
    arguments: Any

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class LLMToolCall:
    id: str
    type: str
    function: LLMFunctionCall

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class LLMMessage:
    role: str
    content: Optional[str]
    function_call: Optional[LLMFunctionCall]
    tool_calls: Optional[List[LLMToolCall]]

    @staticmethod
    def create_message(role: str, content: str):
        return LLMMessage(role=role, content=content, function_call=None, tool_calls=None)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


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
