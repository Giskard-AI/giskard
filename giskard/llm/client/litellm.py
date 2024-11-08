from typing import Any, Dict, Optional, Sequence

from ...client.python_utils import warning
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
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


class LiteLLMClient(LLMClient):
    def __init__(self, model: str = "gpt-4o", completion_params: Optional[Dict[str, Any]] = None):
        """Initialize a LiteLLM completion client

        Parameters
        ----------
        model : str
            The name of the language model to use for text completion. see all supported LLMs: https://docs.litellm.ai/docs/providers/
        completion_params : dict, optional
            A dictionary containing params for the completion.
        """
        self.model = model
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
                temperature=temperature, max_tokens=max_tokens, seed=seed, response_format=_get_response_format(format)
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

        return ChatMessage(role=response_message.role, content=response_message.content)
