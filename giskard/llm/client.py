import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import openai
from git import Sequence
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import LLMConfigurationError
from .errors import LLMGenerationError


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
class LLMOutput:
    message: Optional[str] = None
    function_call: Dict[str, str] = None


@dataclass
class LLMFunctionCall:
    function: str
    args: Any


class LLMLogger:
    def __init__(self):
        self.calls = []
        self.errors = []

    def log_call(self, prompt_tokens, sampled_tokens):
        self.calls.append((prompt_tokens, sampled_tokens))

    def log_error(self, error):
        self.errors.append(error)

    def reset(self):
        self.calls = []

    def get_num_calls(self):
        return len(self.calls)

    def get_num_prompt_tokens(self):
        return sum(c[0] for c in self.calls)

    def get_num_sampled_tokens(self):
        return sum(c[1] for c in self.calls)


class OpenAIClient(LLMClient):
    def __init__(self, openai_api_key=None, openai_organization=None):
        self.openai_api_key = openai_api_key
        self.openai_organization = openai_organization
        self.logger = LLMLogger()

    @retry(retry=retry_if_exception_type(openai.OpenAIError), stop=stop_after_attempt(3), wait=wait_exponential(3))
    def _completion(
        self,
        messages: Sequence,
        model: str,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
    ):
        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                functions=functions,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.openai_api_key,
                organization=self.openai_organization,
            )
        except openai.error.AuthenticationError as err:
            raise LLMConfigurationError(
                "Could not authenticate with OpenAI API. Please make sure you have configured the API either by "
                'setting OPENAI_API_KEY in the environment or using `giskard.llm.set_openai_key("sk-...")`'
            ) from err

        self.logger.log_call(
            prompt_tokens=completion["usage"]["prompt_tokens"], sampled_tokens=completion["usage"]["completion_tokens"]
        )

        return completion.choices[0]["message"]

    def complete(
        self,
        messages,
        functions=None,
        model="gpt-4",
        temperature=0.5,
        max_tokens=None,
        function_call: Optional[Dict] = None,
    ):
        cc = self._completion(
            messages=messages,
            model=model,
            temperature=temperature,
            functions=functions,
            max_tokens=max_tokens,
        )

        function_call = None

        if fc := cc.get("function_call"):
            try:
                function_call = LLMFunctionCall(
                    function=fc["name"],
                    args=json.loads(fc["arguments"]),
                )
            except (json.JSONDecodeError, KeyError) as err:
                raise LLMGenerationError("Could not parse function call") from err

        return LLMOutput(message=cc.content, function_call=function_call)


# Setup the default client
llm_client = OpenAIClient()
