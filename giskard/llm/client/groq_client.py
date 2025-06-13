from typing import Optional, Sequence

from dataclasses import asdict
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

JSON_MODE_GUIDANCE = (
    "To use JSON mode, make sure:\n"
    "1. Pass format='json' or format='json_object' to the `complete()` method.\n"
    "2. You describe the expected JSON structure clearly in the system prompt.\n"
    "3. The selected model supports JSON output.\n"
    "See: https://console.groq.com/docs/text-chat#json-mode"
)

logger = logging.getLogger(__name__)

class GroqClient(LLMClient):
    def __init__(
        self, 
        model: str = "llama-3.3-70b-versatile",  # Default model for Groq
        client: Groq = None,
        #json_mode: Optional[bool] = None
    ):
        logger.info(f"Initializing GroqClient with model: {model}")
        self.model = model
        self._client = client or Groq()
        logger.info("GroqClient initialized successfully")    
    
    def get_config(self) -> dict:
        """Return the configuration of the LLM client."""
        return {
            "client_type": self.__class__.__name__,
            "model": self.model
        }

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format: Optional[str] = None,
    ) -> ChatMessage:
        logger.info(f"GroqClient.complete called with model: {self.model}")
        logger.info(f"Messages: {messages}")
        
        extra_params = dict()

        extra_params["seed"] = seed 

        if format in {"json", "json_object"}:   
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
        
        except groq.BadRequestError as err:
            if format in {"json", "json_object"}:
                raise LLMConfigurationError(
                    f"Model '{self.model}' does not support JSON output or the request format is incorrect.\n\n{JSON_MODE_GUIDANCE}"
                ) from err
            raise  

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion.choices[0].message

        return ChatMessage(role=msg.role, content=msg.content)
