from unittest.mock import Mock, patch

import litellm
import pydantic
import pytest
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from giskard.llm import get_default_client, set_llm_model
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
@pytest.mark.skipif(not PYDANTIC_V2, reason="LiteLLM raise an error with pydantic < 2")
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


API_KEY = "MOCK_API_KEY"


class MockLLM(litellm.CustomLLM):
    def completion(self, model: str, messages: list, api_key: str, **kwargs) -> litellm.ModelResponse:
        assert api_key == API_KEY, "Completion params are not passed properly"

        return litellm.ModelResponse(
            choices=[
                litellm.Choices(
                    model=model,
                    message=litellm.Message(role="assistant", content=f"Mock response - {messages[-1].get('content')}"),
                )
            ]
        )


litellm.custom_provider_map = litellm.custom_provider_map + [{"provider": "mock", "custom_handler": MockLLM()}]


@pytest.mark.skipif(not PYDANTIC_V2, reason="LiteLLM raise an error with pydantic < 2")
def test_litellm_client_custom_model():
    set_llm_model("mock/faux-bot", api_key=API_KEY)

    llm_client = get_default_client()
    message = "Mock input"
    response = llm_client.complete([ChatMessage(role="user", content=message)])
    assert f"Mock response - {message}" == response.content
