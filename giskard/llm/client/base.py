from typing import Any, Dict, Optional

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

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
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
        caller_id: Optional[str] = None,
    ) -> LLMOutput:
        ...

    @abstractmethod
    def embeddings(self, text) -> np.ndarray:
        ...
