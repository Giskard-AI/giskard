import os
from unittest.mock import Mock, patch

import pytest
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import FunctionCall
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

from giskard.llm.client import (
    LLMFunctionCall,
    LLMOutput,
    get_default_client,
    set_llm_api,
    set_llm_model,
)
from giskard.llm.client.openai import LegacyOpenAIClient, OpenAIClient
from tests.utils import TEST_UUID

OLD_OPEN_AI = False
try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    OLD_OPEN_AI = True
    OpenAI = None
    AzureOpenAI = None


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

DEMO_OPENAI_RESPONSE_FC = ChatCompletion(
    id="chatcmpl-abc123",
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(
                content="This is a test!",
                role="assistant",
                function_call=FunctionCall(
                    name="my_test_function", arguments='{\n  "my_parameter": "Parameter Value"\n}'
                ),
            ),
            logprobs=None,
        )
    ],
    created=1677858242,
    model="gpt-3.5-turbo-0613",
    object="chat.completion",
    usage=CompletionUsage(completion_tokens=7, prompt_tokens=13, total_tokens=20),
)

DEMO_OPENAI_RESPONSE_TOOL_CALLS = ChatCompletion(
    id="chatcmpl-abc123",
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(
                content="This is a test!",
                role="assistant",
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id="call_1",
                        function=Function(
                            name="my_test_function", arguments='{\n  "my_parameter": "Parameter Value"\n}'
                        ),
                        type="function",
                    ),
                    ChatCompletionMessageToolCall(
                        id="call_2",
                        function=Function(
                            name="my_test_function", arguments='{\n  "my_parameter": "Another parameter Value"\n}'
                        ),
                        type="function",
                    ),
                ],
            ),
        )
    ],
    created=1677858242,
    model="gpt-3.5-turbo-0613",
    object="chat.completion",
    usage=CompletionUsage(completion_tokens=7, prompt_tokens=13, total_tokens=20),
)

DEMO_LEGACY_OPENAI_RESPONSE = {
    "id": TEST_UUID,
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [{"message": {"role": "assistant", "content": "This is a test!"}, "finish_reason": "stop", "index": 0}],
}

DEMO_LEGACY_OPENAI_RESPONSE_FC = {
    "id": TEST_UUID,
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "This is a test!",
                "function_call": {"name": "my_test_function", "arguments": '{\n  "my_parameter": "Parameter Value"\n}'},
            },
            "finish_reason": "stop",
            "index": 0,
        }
    ],
}

DEMO_LEGACY_OPENAI_RESPONSE_TOOL_CALLS = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "This is a test!",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "my_test_function",
                            "arguments": '{\n  "my_parameter": "Parameter Value"\n}',
                        },
                        "type": "function",
                    },
                    {
                        "id": "call_2",
                        "function": {
                            "name": "my_test_function",
                            "arguments": '{\n  "my_parameter": "Another parameter Value"\n}',
                        },
                        "type": "function",
                    },
                ],
            },
            "finish_reason": "stop",
            "index": 0,
        }
    ],
}


def test_llm_complete_message():
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE
    res = OpenAIClient("gpt-4", client).complete(
        [{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1
    )

    client.chat.completions.create.assert_called_once()
    assert client.chat.completions.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert client.chat.completions.create.call_args[1]["temperature"] == 0.11
    assert client.chat.completions.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert res.function_call is None


@patch("giskard.llm.client.openai.openai")
def test_llm_function_call(openai):
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE_FC

    res = OpenAIClient("gpt-4", client).complete(
        [{"role": "system", "content": "Hello"}], functions=[{"name": "demo"}], temperature=0.11, max_tokens=1
    )

    client.chat.completions.create.assert_called_once()
    assert client.chat.completions.create.call_args[1]["functions"] == [{"name": "demo"}]
    assert client.chat.completions.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert client.chat.completions.create.call_args[1]["temperature"] == 0.11
    assert client.chat.completions.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert isinstance(res.function_call, LLMFunctionCall)
    assert res.function_call.function == "my_test_function"
    assert res.function_call.args == {"my_parameter": "Parameter Value"}


@patch("giskard.llm.client.openai.openai")
def test_llm_tool_calls(openai):
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE_TOOL_CALLS

    res = OpenAIClient("gpt-4", client).complete(
        [{"role": "system", "content": "Hello"}], tools=[{"name": "demo"}], temperature=0.11, max_tokens=1
    )

    client.chat.completions.create.assert_called_once()
    assert client.chat.completions.create.call_args[1]["tools"] == [{"name": "demo"}]
    assert client.chat.completions.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert client.chat.completions.create.call_args[1]["temperature"] == 0.11
    assert client.chat.completions.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert len(res.tool_calls) == 2
    assert res.tool_calls[0].function == "my_test_function"
    assert res.tool_calls[0].args == {"my_parameter": "Parameter Value"}
    assert res.tool_calls[1].function == "my_test_function"
    assert res.tool_calls[1].args == {"my_parameter": "Another parameter Value"}


@patch("giskard.llm.client.openai.openai")
def test_legacy_llm_complete_message(openai):
    openai.ChatCompletion.create.return_value = DEMO_LEGACY_OPENAI_RESPONSE
    res = LegacyOpenAIClient("gpt-4").complete([{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1)

    openai.ChatCompletion.create.assert_called_once()
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert res.function_call is None


@patch("giskard.llm.client.openai.openai")
def test_legacy_llm_function_call(openai):
    openai.ChatCompletion.create.return_value = DEMO_LEGACY_OPENAI_RESPONSE_FC

    res = LegacyOpenAIClient("gpt-4").complete(
        [{"role": "system", "content": "Hello"}], functions=[{"name": "demo"}], temperature=0.11, max_tokens=1
    )

    openai.ChatCompletion.create.assert_called_once()
    assert openai.ChatCompletion.create.call_args[1]["functions"] == [{"name": "demo"}]
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert isinstance(res.function_call, LLMFunctionCall)
    assert res.function_call.function == "my_test_function"
    assert res.function_call.args == {"my_parameter": "Parameter Value"}


@patch("giskard.llm.client.openai.openai")
def test_legacy_llm_tool_calls(openai):
    openai.ChatCompletion.create.return_value = DEMO_LEGACY_OPENAI_RESPONSE_TOOL_CALLS

    res = LegacyOpenAIClient("gpt-4").complete(
        [{"role": "system", "content": "Hello"}], tools=[{"name": "demo"}], temperature=0.11, max_tokens=1
    )

    openai.ChatCompletion.create.assert_called_once()
    assert openai.ChatCompletion.create.call_args[1]["tools"] == [{"name": "demo"}]
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert len(res.tool_calls) == 2
    assert res.tool_calls[0].function == "my_test_function"
    assert res.tool_calls[0].args == {"my_parameter": "Parameter Value"}
    assert res.tool_calls[1].function == "my_test_function"
    assert res.tool_calls[1].args == {"my_parameter": "Another parameter Value"}


@pytest.mark.skipif(OLD_OPEN_AI, reason="Azure is not supported with openai<1.0.0")
def test_autodetect_azure_given_api_in_env():
    os.environ["AZURE_OPENAI_API_KEY"] = "AZURE_OPENAI_API_KEY"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://xxx.openai.azure.com"
    os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"

    set_llm_model("my-gtp-4-model")
    set_llm_api("azure")

    default_client = get_default_client()

    assert isinstance(default_client._client, AzureOpenAI)
    assert default_client.model == "my-gtp-4-model"


@pytest.mark.skipif(OLD_OPEN_AI, reason="Azure is not supported with openai<1.0.0")
def test_autodetect_openai():
    os.environ["OPENAI_API_KEY"] = "sk-..."

    default_client = get_default_client()

    assert isinstance(default_client._client, OpenAI)
