from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


class LLMClient(ABC):
    @abstractmethod
    def estimate_cost(self, num_calls: int, num_prompt_tokens: int, num_sampled_tokens: int, model: str) -> float:
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
