from unittest.mock import Mock, patch

from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import FunctionCall

from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.client.openai import LegacyOpenAIClient, OpenAIClient

DEMO_OPENAI_RESPONSE = ChatCompletion(
    id="chatcmpl-abc123",
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(content="This is a test!", role="assistant", function_call=None),
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
        )
    ],
    created=1677858242,
    model="gpt-3.5-turbo-0613",
    object="chat.completion",
    usage=CompletionUsage(completion_tokens=7, prompt_tokens=13, total_tokens=20),
)

DEMO_LEGACY_OPENAI_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [{"message": {"role": "assistant", "content": "This is a test!"}, "finish_reason": "stop", "index": 0}],
}

DEMO_LEGACY_OPENAI_RESPONSE_FC = {
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
                "function_call": {"name": "my_test_function", "arguments": '{\n  "my_parameter": "Parameter Value"\n}'},
            },
            "finish_reason": "stop",
            "index": 0,
        }
    ],
}


def test_llm_complete_message():
    client = Mock()
    client.chat.completions.create.return_value = DEMO_OPENAI_RESPONSE
    res = OpenAIClient(client).complete([{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1)

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

    res = OpenAIClient(client).complete(
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
def test_legacy_llm_complete_message(openai):
    openai.ChatCompletion.create.return_value = DEMO_LEGACY_OPENAI_RESPONSE
    res = LegacyOpenAIClient().complete([{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1)

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

    res = LegacyOpenAIClient().complete(
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
