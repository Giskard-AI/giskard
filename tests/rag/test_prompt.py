from giskard.llm.client.base import LLMMessage
from giskard.rag.question_generators.prompt import QAGenerationPrompt


def test_qa_generation_prompt():
    prompt = QAGenerationPrompt(
        system_prompt="system prompt {key}",
        user_input_template="user input template {key}",
        example_input="example input",
        example_output="example output",
    )

    messages = prompt.to_messages(
        system_prompt_input={"key": "value1"},
        user_input={"key": "value2"},
    )

    assert len(messages) == 2
    assert isinstance(messages[0], LLMMessage)
    assert messages[0].role == "system"
    assert messages[0].content == "system prompt value1"

    assert isinstance(messages[1], LLMMessage)
    assert messages[1].role == "user"
    assert messages[1].content == "user input template value2"


def test_qa_generation_prompt_with_examples():
    prompt = QAGenerationPrompt(
        system_prompt="system prompt {key}",
        user_input_template="user input template {key}",
        example_input="example input",
        example_output="example output",
    )

    messages = prompt.to_messages(
        system_prompt_input={"key": "value1"}, user_input={"key": "value2"}, add_examples=True
    )

    print(messages)
    assert len(messages) == 4
    assert isinstance(messages[1], LLMMessage)
    assert messages[1].role == "user"
    assert messages[1].content == "example input"
    assert isinstance(messages[2], LLMMessage)
    assert messages[2].role == "assistant"
    assert messages[2].content == "example output"

    messages = prompt.to_messages(
        system_prompt_input={"key": "value1"},
        user_input={"key": "value2"},
        add_examples=True,
        examples=[
            LLMMessage(role="user", content="new example input"),
            LLMMessage(role="assistant", content="new example output"),
        ],
    )
    assert len(messages) == 4
    assert isinstance(messages[1], LLMMessage)
    assert messages[1].role == "user"
    assert messages[1].content == "new example input"
    assert isinstance(messages[2], LLMMessage)
    assert messages[2].role == "assistant"
    assert messages[2].content == "new example output"
