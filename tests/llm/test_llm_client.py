from unittest.mock import Mock

from mistralai.models.chat_completion import ChatCompletionResponse, ChatCompletionResponseChoice
from mistralai.models.chat_completion import ChatMessage as MistralChatMessage
from mistralai.models.chat_completion import FinishReason, UsageInfo
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from giskard.llm.client import ChatMessage
from giskard.llm.client.mistral import MistralClient
from giskard.llm.client.openai import OpenAIClient

DEMO_OPENAI_RESPONSE = ChatCompletion(
    id="chatcmpl-abc123",
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(content="This is a test!", role="assistant", function_call=None),
            logprobs=None,
        )
    ],
    created=1677858242,
    model="gpt-3.5-turbo-0613",
    object="chat.completion",
    usage=CompletionUsage(completion_tokens=7, prompt_tokens=13, total_tokens=20),
)


DEMO_MISTRAL_RESPONSE = ChatCompletionResponse(
    id="2d62260a7a354e02922a4f6ad36930d3",
    object="chat.completion",
    created=1630000000,
    model="mistral-large",
    choices=[
        ChatCompletionResponseChoice(
            index=0,
            message=MistralChatMessage(role="assistant", content="This is a test!", name=None, tool_calls=None),
            finish_reason=FinishReason.stop,
        )
    ],
    usage=UsageInfo(prompt_tokens=9, total_tokens=89, completion_tokens=80),
)


def test_llm_complete_message():
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE
    res = OpenAIClient("gpt-35-turbo", client).complete(
        [ChatMessage(role="system", content="Hello")], temperature=0.11, max_tokens=1
    )

    client.chat.completions.create.assert_called_once()
    assert client.chat.completions.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert client.chat.completions.create.call_args[1]["temperature"] == 0.11
    assert client.chat.completions.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"


def test_mistral_client():
    client = Mock()
    client.chat.return_value = DEMO_MISTRAL_RESPONSE

    res = MistralClient(model="mistral-large", client=client).complete(
        [ChatMessage(role="user", content="Hello")], temperature=0.11, max_tokens=12
    )

    client.chat.assert_called_once()
    assert client.chat.call_args[1]["messages"] == [MistralChatMessage(role="user", content="Hello")]
    assert client.chat.call_args[1]["temperature"] == 0.11
    assert client.chat.call_args[1]["max_tokens"] == 12

    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"
