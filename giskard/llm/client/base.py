from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self,
        messages,
        functions=None,
        model="gpt-4",
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
    ):
        ...


@dataclass
class LLMFunctionCall:
    function: str
    args: Any


@dataclass
class LLMOutput:
    message: Optional[str] = None
    function_call: Optional[LLMFunctionCall] = None
