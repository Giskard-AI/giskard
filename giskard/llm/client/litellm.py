from typing import Any, Dict, Optional, Sequence

import json
import logging
import os
import re

from ...client.python_utils import warning
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

logger = logging.getLogger(__name__)

try:
    os.environ["LITELLM_LOG"] = "ERROR"
    import litellm
except ImportError as err:
    raise LLMImportError(flavor="litellm") from err


def _get_response_format(format):
    if format is None:
        return None

    if format in ("json", "json_object"):
        return {"type": format}

    warning(f"Unsupported format '{format}', ignoring.")
    return None


def _trim_json(response_message: str):
    if "{" not in response_message or "}" not in response_message:
        return response_message

    json_start = response_message.index("{")
    json_end = len(response_message) - response_message[::-1].index("}")

    return response_message if json_start > json_end else response_message[json_start:json_end]


def _parse_json_output(
    raw_json: str, llm_client: LLMClient, keys: Optional[Sequence[str]] = None, caller_id: Optional[str] = None
) -> dict:
    try:
        return json.loads(_trim_json(raw_json), strict=False)
    except json.JSONDecodeError:
        logger.debug("JSON decoding error, trying to fix the JSON string.")

    logger.debug("Raw output: %s", raw_json)
    # Let's see if it's just a matter of markdown format (```json ... ```)
    match = re.search(r"```json\s{0,5}(.*?)\s{0,5}```", raw_json, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1), strict=False)
        except json.JSONDecodeError:
            logger.debug("String matching didn't fix the format, trying to fix it with the LLM itself.")

    # Final attempt, let's try to fix the JSON with the LLM itself
    out = llm_client.complete(
        messages=[
            ChatMessage(
                role="system",
                content="Fix the following text so it contains a single valid JSON object. You answer MUST start and end with curly brackets.",
            ),
            ChatMessage(role="user", content=raw_json),
        ],
        temperature=0,
        caller_id=caller_id,
    )

    parsed_dict = json.loads(_trim_json(out.content), strict=False)

    if keys is not None and any([k not in parsed_dict for k in keys]):
        raise ValueError(f"Keys {keys} not found in the JSON output: {parsed_dict}")

    return parsed_dict


class LiteLLMClient(LLMClient):
    def __init__(
        self,
        model: str = "gpt-4o",
        disable_structured_output: bool = False,
        completion_params: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a LiteLLM completion client

        Parameters
        ----------
        model : str
            The name of the language model to use for text completion. see all supported LLMs: https://docs.litellm.ai/docs/providers/
        completion_params : dict, optional
            A dictionary containing params for the completion.
        """
        self.model = model
        self.disable_structured_output = disable_structured_output
        self.completion_params = completion_params or dict()

    def _build_supported_completion_params(self, **kwargs):
        supported_params = litellm.get_supported_openai_params(model=self.model)

        return {
            param_name: param_value
            for param_name, param_value in kwargs.items()
            if supported_params is None or param_name in supported_params
        }

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        completion = litellm.completion(
            model=self.model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            **self._build_supported_completion_params(
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                response_format=None if self.disable_structured_output else _get_response_format(format),
            ),
            **self.completion_params,
        )

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        response_message = completion.choices[0].message
        if format in ("json", "json_object"):
            # Max 3 attempts to parse the JSON output
            for i in range(3):
                try:
                    json_dict = _parse_json_output(response_message.content, self, caller_id=caller_id)
                    response_message.content = json.dumps(json_dict)
                    break
                except ValueError as e:
                    if i == 2:
                        raise e
                    response_message = completion.choices[i + 1].message
                    continue

        return ChatMessage(role=response_message.role, content=response_message.content)
