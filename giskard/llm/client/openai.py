import json
from abc import ABC, abstractmethod
from typing import Dict, Optional, Sequence

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import LLMConfigurationError
from ..errors import LLMGenerationError, LLMImportError
from . import LLMClient, LLMFunctionCall, LLMLogger, LLMOutput

try:
    import openai
except ImportError as err:
    raise LLMImportError(flavor="llm") from err

AUTH_ERROR_MESSAGE = (
    "Could not authenticate with OpenAI API. Please make sure you have configured the API key by "
    "setting OPENAI_API_KEY in the environment."
)


class BaseOpenAIClient(LLMClient, ABC):
    def __init__(self):
        self._logger = LLMLogger()

    @property
    def logger(self) -> LLMLogger:
        return self._logger

    @abstractmethod
    def _completion(
        self,
        messages: Sequence,
        model: str,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
    ) -> dict:
        ...

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
        cc = self._completion(
            messages=messages,
            model=model,
            temperature=temperature,
            functions=functions,
            function_call=function_call,
            max_tokens=max_tokens,
            caller_id=caller_id,
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

        return LLMOutput(message=cc["content"], function_call=function_call)


class LegacyOpenAIClient(BaseOpenAIClient):
    """OpenAI client for versions <= 0.28.1"""

    def __init__(self, openai_api_key=None, openai_organization=None):
        self.openai_api_key = openai_api_key
        self.openai_organization = openai_organization
        super().__init__()

    @retry(retry=retry_if_exception_type(openai.OpenAIError), stop=stop_after_attempt(3), wait=wait_exponential(3))
    def _completion(
        self,
        messages: Sequence,
        model: str,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
    ):
        extra_params = dict()
        if function_call is not None:
            extra_params["function_call"] = function_call
        if functions is not None:
            extra_params["functions"] = functions

        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
                api_key=self.openai_api_key,
                organization=self.openai_organization,
            )
        except openai.error.AuthenticationError as err:
            raise LLMConfigurationError(AUTH_ERROR_MESSAGE) from err

        self._logger.log_call(
            prompt_tokens=completion["usage"]["prompt_tokens"],
            sampled_tokens=completion["usage"]["completion_tokens"],
            model=model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        return completion["choices"][0]["message"]


class OpenAIClient(BaseOpenAIClient):
    def __init__(self, client=None):
        self._client = client or openai.OpenAI()
        super().__init__()

    def _completion(
        self,
        messages: Sequence,
        model: str,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
    ):
        extra_params = dict()
        if function_call is not None:
            extra_params["function_call"] = function_call
        if functions is not None:
            extra_params["functions"] = functions

        try:
            completion = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
        except openai.AuthenticationError as err:
            raise LLMConfigurationError(AUTH_ERROR_MESSAGE) from err

        self._logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        return completion.choices[0].message.model_dump()
