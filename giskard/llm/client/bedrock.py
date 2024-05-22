from typing import Optional, Sequence

import json

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


class ClaudeBedrockClient(LLMClient):
    def __init__(
        self,
        bedrock_runtime_client,
        model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        anthropic_version: str = "bedrock-2023-05-31",
    ):
        self._client = bedrock_runtime_client
        self.model = model
        self.anthropic_version = anthropic_version

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1,
        max_tokens: Optional[int] = 1000,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        # only supporting claude 3 to start
        if "claude-3" not in self.model:
            raise LLMConfigurationError(f"Only claude-3 models are supported as of now, got {self.model}")

        # Create the messages format needed for bedrock specifically
        input_msg_prompt = []
        system_prompts = []
        for msg in messages:
            if msg.role.lower() == "system":
                system_prompts = system_prompts.append(msg.content)
            elif msg.role.lower() == "assistant":
                input_msg_prompt.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
            else:
                input_msg_prompt.append({"role": "user", "content": [{"type": "text", "text": msg.content}]})

        # create the json body to send to the API
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": "\n".join(system_prompts),
                "messages": input_msg_prompt,
            }
        )

        # invoke the model and get the response
        try:
            accept = "application/json"
            contentType = "application/json"
            response = self._client.invoke_model(body=body, modelId=self.model, accept=accept, contentType=contentType)
            completion = json.loads(response.get("body").read())
        except RuntimeError as err:
            raise LLMConfigurationError("Could not get response from Bedrock API") from err

        self.logger.log_call(
            prompt_tokens=completion["usage"]["input_tokens"],
            sampled_tokens=completion["usage"]["input_tokens"],
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion["content"][0]["text"]
        return ChatMessage(role="assistant", content=msg)
