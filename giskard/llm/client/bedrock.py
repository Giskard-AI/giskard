from typing import Dict, List, Optional, Sequence

import json
from abc import ABC, abstractmethod

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
    import boto3  # noqa: F401
except ImportError as err:
    raise LLMImportError(
        flavor="llm", msg="To use Bedrock models, please install the `boto3` package with `pip install boto3`"
    ) from err


class BaseBedrockClient(LLMClient, ABC):
    def __init__(self, bedrock_runtime_client, model: str):
        self._client = bedrock_runtime_client
        self.model = model

    @abstractmethod
    def _format_body(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = 1000,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> Dict:
        ...

    @abstractmethod
    def _parse_completion(self, completion, caller_id: Optional[str] = None) -> ChatMessage:
        ...

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = 1000,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        # create the json body to send to the API
        body = self._format_body(messages, temperature, max_tokens, caller_id, seed, format)

        # invoke the model and get the response
        try:
            accept = "application/json"
            contentType = "application/json"
            response = self._client.invoke_model(body=body, modelId=self.model, accept=accept, contentType=contentType)
            completion = json.loads(response.get("body").read())
        except RuntimeError as err:
            raise LLMConfigurationError("Could not get response from Bedrock API") from err

        return self._parse_completion(completion, caller_id)


class ClaudeBedrockClient(BaseBedrockClient):
    def __init__(
        self,
        bedrock_runtime_client,
        model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        anthropic_version: str = "bedrock-2023-05-31",
    ):
        # only supporting claude 3
        if "claude-3" not in model:
            raise LLMConfigurationError(f"Only claude-3 models are supported as of now, got {self.model}")

        super().__init__(bedrock_runtime_client, model)
        self.anthropic_version = anthropic_version

    def _format_body(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = 1000,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> Dict:
        input_msg_prompt: List = []
        system_prompts = []

        for msg in messages:
            # System prompt is a specific parameter in Claude
            if msg.role.lower() == "system":
                system_prompts.append(msg.content)
                continue

            # Only role user and assistant are allowed
            role = msg.role.lower()
            role = role if role in ["assistant", "user"] else "user"

            # Consecutive messages need to be grouped
            last_message = None if len(input_msg_prompt) == 0 else input_msg_prompt[-1]
            if last_message is not None and last_message["role"] == role:
                last_message["content"].append({"type": "text", "text": msg.content})
                continue

            input_msg_prompt.append({"role": role, "content": [{"type": "text", "text": msg.content}]})

        return json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": "\n".join(system_prompts),
                "messages": input_msg_prompt,
            }
        )

    def _parse_completion(self, completion, caller_id: Optional[str] = None) -> ChatMessage:
        self.logger.log_call(
            prompt_tokens=completion["usage"]["input_tokens"],
            sampled_tokens=completion["usage"]["output_tokens"],
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion["content"][0]["text"]
        return ChatMessage(role="assistant", content=msg)


class LLamaBedrockClient(BaseBedrockClient):
    def __init__(self, bedrock_runtime_client, model: str = "meta.llama3-8b-instruct-v1:0"):
        # only supporting llama
        if "llama" not in model:
            raise LLMConfigurationError(f"Only Llama models are supported as of now, got {self.model}")

        super().__init__(bedrock_runtime_client, model)

    def _format_body(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = 1000,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> Dict:
        # Create the messages format needed for llama bedrock specifically
        prompts = []
        for msg in messages:
            prompts.append(f"# {msg.role}:\n{msg.content}\n")

        # create the json body to send to the API
        messages = "\n".join(prompts)
        return json.dumps(
            {
                "max_gen_len": max_tokens,
                "temperature": temperature,
                "prompt": f"{messages}\n# assistant:\n",
            }
        )

    def _parse_completion(self, completion, caller_id: Optional[str] = None) -> ChatMessage:
        self.logger.log_call(
            prompt_tokens=completion["prompt_token_count"],
            sampled_tokens=completion["generation_token_count"],
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion["generation"]
        return ChatMessage(role="assistant", content=msg)
