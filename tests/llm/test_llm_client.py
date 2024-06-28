import json
from unittest.mock import MagicMock, Mock

import pydantic
import pytest
from google.generativeai.types import ContentDict
from mistralai.models.chat_completion import ChatCompletionResponse, ChatCompletionResponseChoice
from mistralai.models.chat_completion import ChatMessage as MistralChatMessage
from mistralai.models.chat_completion import FinishReason, UsageInfo
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from giskard.llm.client import ChatMessage
from giskard.llm.client.bedrock import ClaudeBedrockClient
from giskard.llm.client.gemini import GeminiClient
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


@pytest.mark.skipif(not PYDANTIC_V2, reason="Mistral raise an error with pydantic < 2")
def test_mistral_client():
    client = Mock()
    client.chat.return_value = DEMO_MISTRAL_RESPONSE

    from giskard.llm.client.mistral import MistralClient

    res = MistralClient(model="mistral-large", client=client).complete(
        [ChatMessage(role="user", content="Hello")], temperature=0.11, max_tokens=12
    )

    client.chat.assert_called_once()
    assert client.chat.call_args[1]["messages"] == [MistralChatMessage(role="user", content="Hello")]
    assert client.chat.call_args[1]["temperature"] == 0.11
    assert client.chat.call_args[1]["max_tokens"] == 12

    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"


def test_claude_bedrock_client():
    # Mock the bedrock_runtime_client
    bedrock_runtime_client = Mock()
    bedrock_runtime_client.invoke_model = MagicMock(
        return_value={
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {
                            "id": "chatcmpl-abc123",
                            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "text", "text": "This is a test!"}],
                            "stop_reason": "end_turn",
                            "usage": {
                                "input_tokens": 9,
                                "output_tokens": 89,
                            },
                        }
                    )
                )
            )
        }
    )

    # Initialize the ClaudeBedrockClient with the mocked bedrock_runtime_client
    client = ClaudeBedrockClient(
        bedrock_runtime_client, model="anthropic.claude-3-sonnet-20240229-v1:0", anthropic_version="bedrock-2023-05-31"
    )

    # Call the complete method
    res = client.complete([ChatMessage(role="user", content="Hello")], temperature=0.11, max_tokens=12)

    # Assert that the invoke_model method was called with the correct arguments
    bedrock_runtime_client.invoke_model.assert_called_once()

    # Assert that the response is a ChatMessage and has the correct content
    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"


def test_gemini_client():
    # Mock the Gemini client
    gemini_api_client = Mock()
    gemini_api_client.generate_content = MagicMock(
        return_value=Mock(text="This is a test!", candidates=[Mock(content=Mock(role="assistant"))])
    )
    gemini_api_client.count_tokens = MagicMock(
        side_effect=lambda text: sum(len(t.split()) for t in text) if isinstance(text, list) else len(text.split())
    )

    # Initialize the GeminiClient with the mocked gemini_api_client
    client = GeminiClient(model="gemini-pro", _client=gemini_api_client)

    # Call the complete method
    res = client.complete([ChatMessage(role="user", content="Hello")], temperature=0.11, max_tokens=12)
    print(res)

    # Assert that the generate_content method was called with the correct arguments
    gemini_api_client.generate_content.assert_called_once()
    assert gemini_api_client.generate_content.call_args[1]["contents"] == ([ContentDict(role="user", parts=["Hello"])])
    assert gemini_api_client.generate_content.call_args[1]["generation_config"].temperature == 0.11
    assert gemini_api_client.generate_content.call_args[1]["generation_config"].max_output_tokens == 12

    # Assert that the response is a ChatMessage and has the correct content
    assert isinstance(res, ChatMessage)
    assert res.content == "This is a test!"
