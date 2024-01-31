from typing import Dict, List, Optional, Sequence

import json
from abc import ABC, abstractmethod

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import LLMConfigurationError
from ..errors import LLMGenerationError, LLMImportError
from . import LLMClient, LLMFunctionCall, LLMLogger, LLMMessage
from .base import LLMToolCall

try:
    import openai
except ImportError as err:
    raise LLMImportError(flavor="llm") from err

AUTH_ERROR_MESSAGE = (
    "Could not authenticate with OpenAI API. Please make sure you have configured the API key by "
    "setting OPENAI_API_KEY in the environment."
)


class BaseOpenAIClient(LLMClient, ABC):
    def __init__(self, model: str):
        self._logger = LLMLogger()
        self.model = model

    @property
    def logger(self) -> LLMLogger:
        return self._logger

    @abstractmethod
    def _completion(
        self,
        messages: Sequence,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
    ) -> dict:
        ...

    @staticmethod
    def _parse_function_call(function_call) -> LLMFunctionCall:
        try:
            return LLMFunctionCall(
                name=function_call["name"],
                arguments=json.loads(function_call["arguments"]),
            )
        except (json.JSONDecodeError, KeyError) as err:
            raise LLMGenerationError("Could not parse function call") from err

    @staticmethod
    def _parse_tool_call(tool_call) -> LLMToolCall:
        return LLMToolCall(
            id=tool_call["id"],
            type=tool_call["type"],
            function=BaseOpenAIClient._parse_function_call(tool_call["function"]),
        )

    @staticmethod
    def _parse_tool_calls(tool_calls) -> List[LLMToolCall]:
        return [BaseOpenAIClient._parse_tool_call(tool_call) for tool_call in tool_calls]

    @staticmethod
    def _parse_message(response) -> LLMMessage:
        return LLMMessage(
            role=response["role"],
            content=response["content"],
            function_call=BaseOpenAIClient._parse_function_call(response["function_call"])
            if "function_call" in response and response["function_call"] is not None
            else None,
            tool_calls=BaseOpenAIClient._parse_tool_calls(response["tool_calls"])
            if "tool_calls" in response and response["tool_calls"] is not None
            else None,
        )

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
    ):
        llm_message = self._completion(
            messages=[
                message.model_dump(exclude_none=True) if isinstance(message, LLMMessage) else message
                for message in messages
            ],
            temperature=temperature,
            functions=functions,
            function_call=function_call,
            max_tokens=max_tokens,
            caller_id=caller_id,
            tools=tools,
            tool_choice=tool_choice,
        )

        return BaseOpenAIClient._parse_message(llm_message)


class LegacyOpenAIClient(BaseOpenAIClient):
    """OpenAI client for versions <= 0.28.1"""

    def __init__(self, model: str, openai_api_key=None, openai_organization=None):
        self.openai_api_key = openai_api_key
        self.openai_organization = openai_organization
        super().__init__(model)

    @retry(retry=retry_if_exception_type(openai.OpenAIError), stop=stop_after_attempt(3), wait=wait_exponential(3))
    def _completion(
        self,
        messages: Sequence,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
    ):
        extra_params = dict()
        if function_call is not None:
            extra_params["function_call"] = function_call
        if functions is not None:
            extra_params["functions"] = functions
        if tools is not None:
            extra_params["tools"] = tools
        if tool_choice is not None:
            extra_params["tool_choice"] = tool_choice

        try:
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    message.model_dump(exclude_none=True) if isinstance(message, LLMMessage) else message
                    for message in messages
                ],
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
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        return completion["choices"][0]["message"]


class OpenAIClient(BaseOpenAIClient):
    def __init__(self, model: str, client=None):
        self._client = client or openai.OpenAI()

        super().__init__(model)

    def _completion(
        self,
        messages: Sequence,
        functions: Sequence = None,
        temperature: float = 1.0,
        function_call: Optional[Dict] = None,
        max_tokens=None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
    ):
        extra_params = dict()
        if function_call is not None:
            extra_params["function_call"] = function_call
        if functions is not None:
            extra_params["functions"] = functions
        if tools is not None:
            extra_params["tools"] = tools
        if tool_choice is not None:
            extra_params["tool_choice"] = tool_choice

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
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
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        return completion.choices[0].message.model_dump()
