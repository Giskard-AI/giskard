from unittest.mock import Mock, patch

import pydantic
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from giskard.llm.client import ChatMessage
from giskard.llm.client.litellm import LiteLLMClient
from giskard.llm.client.openai import OpenAIClient

PYDANTIC_V2 = pydantic.__version__.startswith("2.")

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


@patch("litellm.completion")
def test_litellm_client(completion):
    completion.return_value = DEMO_OPENAI_RESPONSE
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE
    res = LiteLLMClient("gpt-4o", {"api_key": "api_key"}).complete(
        [ChatMessage(role="system", content="Hello")], temperature=0.11, max_tokens=1
    )

    completion.assert_called_once()
    assert completion.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert completion.call_args[1]["temperature"] == 0.11
    assert completion.call_args[1]["max_tokens"] == 1
    assert completion.call_args[1]["api_key"] == "api_key"
    assert completion.call_args[1]["model"] == "gpt-4o"

    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"
