from giskard.llm.client.base import ChatMessage
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
        add_examples=False,
    )

    assert len(messages) == 2
    assert isinstance(messages[0], ChatMessage)
    assert messages[0].role == "system"
    assert messages[0].content == "system prompt value1"

    assert isinstance(messages[1], ChatMessage)
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
    assert isinstance(messages[1], ChatMessage)
    assert messages[1].role == "user"
    assert messages[1].content == "example input"
    assert isinstance(messages[2], ChatMessage)
    assert messages[2].role == "assistant"
    assert messages[2].content == "example output"

    messages = prompt.to_messages(
        system_prompt_input={"key": "value1"},
        user_input={"key": "value2"},
        add_examples=True,
        examples=[
            ChatMessage(role="user", content="new example input"),
            ChatMessage(role="assistant", content="new example output"),
        ],
    )
    assert len(messages) == 4
    assert isinstance(messages[1], ChatMessage)
    assert messages[1].role == "user"
    assert messages[1].content == "new example input"
    assert isinstance(messages[2], ChatMessage)
    assert messages[2].role == "assistant"
    assert messages[2].content == "new example output"
