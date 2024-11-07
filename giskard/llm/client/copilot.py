from typing import Optional, Sequence

from dataclasses import dataclass
from logging import warning

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from .base import ChatMessage
from .openai import AUTH_ERROR_MESSAGE, OpenAIClient

try:
    import openai
    from openai.types.chat import ChatCompletionMessageToolCall
except ImportError as err:
    raise LLMImportError(flavor="talk") from err


@dataclass
class ToolChatMessage(ChatMessage):
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list["ChatCompletionMessageToolCall"]] = None


def _format_message(msg: ChatMessage) -> dict:
    """Format chat message.
    Based on a message's role, include related attributes and exclude non-related.
    Parameters
    ----------
    msg : ChatMessage
        Message to the LLMClient.
    Returns
    -------
    dict
        A dictionary with attributes related to the role.
    """
    fmt_msg = {"role": msg.role, "content": msg.content}
    if msg.role == "tool":
        fmt_msg.update({"name": msg.name, "tool_call_id": msg.tool_call_id})
    if msg.role == "assistant" and msg.tool_calls:
        fmt_msg.update({"tool_calls": msg.tool_calls})
    return fmt_msg


class GiskardCopilotClient(OpenAIClient):
    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        tools=None,
        tool_choice=None,
        seed: Optional[int] = None,
        format=None,
    ) -> ToolChatMessage:
        extra_params = dict()

        if tools is not None:
            extra_params["tools"] = tools
        if tool_choice is not None:
            extra_params["tool_choice"] = tool_choice

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
                messages=[_format_message(m) for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
        except openai.AuthenticationError as err:
            raise LLMConfigurationError(AUTH_ERROR_MESSAGE) from err

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion.choices[0].message

        return ToolChatMessage(role=msg.role, content=msg.content, tool_calls=msg.tool_calls)
