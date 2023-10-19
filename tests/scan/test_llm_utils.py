from unittest.mock import patch

import openai

from giskard.llm.utils import llm, llm_fn_call

RAW_DEMO_OPENAI_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
    "choices": [{"message": {"role": "assistant", "content": "This is a test!"}, "finish_reason": "stop", "index": 0}],
}

DEMO_OPENAI_RESPONSE = openai.openai_object.OpenAIObject.construct_from(RAW_DEMO_OPENAI_RESPONSE)


@patch("giskard.scanner.llm.utils.openai")
def test_llm_call(openai):
    openai.ChatCompletion.create.return_value = DEMO_OPENAI_RESPONSE
    res = llm([{"role": "system", "content": "Hello"}], temperature=0.11, max_tokens=1)

    assert openai.ChatCompletion.create.call_count == 1
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert res == "This is a test!"


@patch("giskard.scanner.llm.utils.openai")
def test_llm_function_call(openai):
    openai.ChatCompletion.create.return_value = DEMO_OPENAI_RESPONSE

    res = llm_fn_call(
        [{"role": "system", "content": "Hello"}], functions=[{"name": "demo"}], temperature=0.11, max_tokens=1
    )

    assert openai.ChatCompletion.create.call_count == 1
    assert openai.ChatCompletion.create.call_args[1]["functions"] == [{"name": "demo"}]
    assert openai.ChatCompletion.create.call_args[1]["messages"] == [{"role": "system", "content": "Hello"}]
    assert openai.ChatCompletion.create.call_args[1]["temperature"] == 0.11
    assert openai.ChatCompletion.create.call_args[1]["max_tokens"] == 1

    assert res == {"role": "assistant", "content": "This is a test!"}
