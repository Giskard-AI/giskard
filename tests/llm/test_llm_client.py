from unittest.mock import patch

import openai

from giskard.llm.client import LLMFunctionCall, LLMOutput, llm_client

RAW_DEMO_OPENAI_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [{"message": {"role": "assistant", "content": "This is a test!"}, "finish_reason": "stop", "index": 0}],
}

RAW_DEMO_OPENAI_RESPONSE_WITH_FUNCTION_CALL = {
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
                "function_call": {
                    "name": "my_test_function",
                    "arguments": '{\n  "my_parameter": "Parameter Value"\n}',
                },
            },
            "finish_reason": "stop",
            "index": 0,
        }
    ],
}

DEMO_OPENAI_RESPONSE = openai.openai_object.OpenAIObject.construct_from(RAW_DEMO_OPENAI_RESPONSE)
DEMO_OPENAI_RESPONSE_FC = openai.openai_object.OpenAIObject.construct_from(RAW_DEMO_OPENAI_RESPONSE_WITH_FUNCTION_CALL)


@patch("giskard.llm.client.openai")
def test_llm_complete_message(openai):
    openai.ChatCompletion.create.return_value = DEMO_OPENAI_RESPONSE
    res = llm_client.complete([{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1)

    openai.ChatCompletion.create.assert_called_once()
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert isinstance(res, LLMOutput)
    assert res.message == "This is a test!"
    assert res.function_call is None


@patch("giskard.llm.utils.openai")
def test_llm_function_call(openai):
    openai.ChatCompletion.create.return_value = DEMO_OPENAI_RESPONSE_FC

    res = llm_client.complete(
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
    assert res.function_call.arguments == {"my_parameter": "Parameter Value"}
