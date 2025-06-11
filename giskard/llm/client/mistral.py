from typing import Optional, Sequence
from typing_extensions import deprecated

import os
from dataclasses import asdict
from logging import warning

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
    from mistralai import Mistral
except ImportError as err:
    raise LLMImportError(
        flavor="llm", msg="To use Mistral models, please install the `mistralai` package with `pip install mistralai`"
    ) from err


@deprecated("MistralClient is deprecated: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html")
class MistralClient(LLMClient):
    def __init__(self, model: str = "mistral-large-latest", client: Mistral = None):
        self.model = model
        self._client = client or Mistral(api_key=os.getenv("MISTRAL_API_KEY", ""))

    def get_config(self) -> dict:
        """Return the configuration of the LLM client."""
        return {"client_type": self.__class__.__name__, "model": self.model}

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format: str = None,
    ) -> ChatMessage:
        extra_params = dict()
        if seed is not None:
            extra_params["random_seed"] = seed

        if format not in (None, "json", "json_object") and "large" not in self.model:
            warning(f"Unsupported format '{format}', ignoring.")
            format = None

        if format == "json" or format == "json_object":
            extra_params["response_format"] = {"type": "json_object"}

        try:
            completion = self._client.chat.complete(
                model=self.model,
                messages=[asdict(m) for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
        except RuntimeError as err:
            raise LLMConfigurationError("Could not get response from Mistral API") from err

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion.choices[0].message

        return ChatMessage(role=msg.role, content=msg.content)
