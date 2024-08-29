from typing import Optional, Sequence

from logging import warning

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
    import google.generativeai as genai
    from google.generativeai.types import ContentDict
except ImportError as err:
    raise LLMImportError(
        flavor="llm",
        msg="To use Gemini models, please install the `genai` package with `pip install google-generativeai`",
    ) from err

AUTH_ERROR_MESSAGE = (
    "Could not get Response from Gemini API. Please make sure you have configured the API key by "
    "setting GOOGLE_API_KEY in the environment."
)


def _format(messages: Sequence[ChatMessage]) -> Sequence[ContentDict]:
    system_prompts = []
    content = []

    for message in messages:
        if message.role == "system":
            system_prompts.append(message.content)

            if len(content) == 0:
                content.append(ContentDict(role="model", parts=[]))

            content[0]["parts"].insert(0, f"# System:\n{message.content}")

            continue

        role = "model" if message.role == "assistant" else "user"

        # Consecutive messages need to be grouped
        last_message = None if len(content) == 0 else content[-1]
        if last_message is not None and last_message["role"] == role:
            last_message["parts"].append(message.content)
            continue

        content.append(ContentDict(role=role, parts=[message.content]))

    return content


class GeminiClient(LLMClient):
    def __init__(self, model: str = "gemini-pro", _client=None):
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
        if seed is not None:
            warning("Unsupported seed, ignoring.")

        if format:
            warning(f"Unsupported format '{format}', ignoring.")

        try:
            completion = self._client.generate_content(
                contents=_format(messages),
                generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
            )
        except RuntimeError as err:
            raise LLMConfigurationError(AUTH_ERROR_MESSAGE) from err

        self.logger.log_call(
            prompt_tokens=self._client.count_tokens([m.content for m in messages]).total_tokens,
            sampled_tokens=self._client.count_tokens(completion.text).total_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        # Assuming the response structure is similar to the ChatMessage structure
        return ChatMessage(role=completion.candidates[0].content.role, content=completion.text)
