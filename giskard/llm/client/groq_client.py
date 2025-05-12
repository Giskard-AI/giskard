from typing import Optional, Sequence

from dataclasses import asdict
from logging import warning
import logging

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
    from groq import Groq
    import groq
except ImportError as err:
    raise LLMImportError(flavor="llm") from err

AUTH_ERROR_MESSAGE = (
    "Could not authenticate with Groq API. Please make sure you have configured the API key by "
    "setting GROQ_API_KEY in the environment."
)

def _supports_json_format(model: str) -> bool:
    if "llama-3.3-70b-versatile" in model:
        return True

    if model == "llama-3.1-8b-instant" or model == "gemma2-9b-it":
        return True

    return False

logger = logging.getLogger(__name__)

class GroqClient(LLMClient):
    def __init__(
        self, 
        model: str = "llama-3.3-70b-versatile",  # Default model for Groq
        client: Groq = None,
        json_mode: Optional[bool] = None
    ):
        logger.info(f"Initializing GroqClient with model: {model}")
        self.model = model
        self._client = client or Groq()
        self.json_mode = json_mode if json_mode is not None else _supports_json_format(model)
        logger.info("GroqClient initialized successfully")

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        logger.info(f"GroqClient.complete called with model: {self.model}")
        logger.info(f"Messages: {messages}")
        
        extra_params = dict()

        if seed is not None:
            extra_params["seed"] = seed

        if self.json_mode:
            if format not in (None, "json", "json_object"):
                warning(f"Unsupported format '{format}', ignoring.")
                format = None

            if format == "json" or format == "json_object":
                extra_params["response_format"] = {"type": "json_object"}

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[asdict(m) for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
        except groq.AuthenticationError as err: 
            raise LLMConfigurationError(AUTH_ERROR_MESSAGE) from err

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion.choices[0].message

        return ChatMessage(role=msg.role, content=msg.content)