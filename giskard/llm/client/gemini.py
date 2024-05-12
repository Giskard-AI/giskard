from typing import Optional, Sequence
from logging import warning
from dataclasses import asdict
from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage
from google.generativeai.types import ContentDict
import os

try:
    import google.generativeai as genai
except ImportError as err:
    raise LLMImportError(
        flavor="llm", msg="To use Gemini models, please install the `genai` package with `pip install google-generativeai`"
    ) from err

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

AUTH_ERROR_MESSAGE = (
    "Could not authenticate with Gemini API. Please make sure you have configured the API key by "
    "setting GOOGLE_API_KEY in the environment."
)

def _to_content_dict(messages: Sequence[ChatMessage]) -> Sequence[ContentDict]: 
    return [ContentDict(role=m.role, parts=m.content) for m in messages]
    
class GeminiClient(LLMClient):
    def __init__(self, model: str = "gemini-pro", _client=None ):
        self.model = model
        self._client = _client or genai.GenerativeModel(self.model)

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
        format=None,
    ) -> ChatMessage:
        extra_params = dict()
        if seed is not None:
            extra_params["seed"] = seed

        if format:
            warning(f"Unsupported format '{format}', ignoring.")
            format = None

        try:
            completion = self._client.generate_content(
                contents=_to_content_dict(messages),
                generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **extra_params,)
            )
        except RuntimeError as err:
            raise LLMConfigurationError("Could not get response from Gemini API") from err

        prompt_tokens = self._client.count_tokens([m.content for m in messages])
        completion_tokens = self._client.count_tokens(completion.text)
        
        self.logger.log_call(
            prompt_tokens=prompt_tokens,
            sampled_tokens=completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        # Assuming the response structure is similar to the ChatMessage structure
        return ChatMessage(role=completion.candidates[0].content.role, content=completion.text)
