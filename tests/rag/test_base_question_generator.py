import logging
from unittest.mock import Mock

from giskard.llm.client.base import LLMMessage
from giskard.rag.question_generators.simple_questions import SimpleQuestionGenerator


def test_base_generator():
    llm_client = Mock()
    llm_client.complete = Mock(
        return_value=LLMMessage(
            role="assistant",
            content='{"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France."}',
        )
    )

    base_generator = SimpleQuestionGenerator(llm_client=llm_client)
    completion = base_generator._llm_complete(messages=[])

    assert isinstance(completion, dict)
    assert completion["question"] == "Where is Camembert from?"
    assert completion["answer"] == "Camembert was created in Normandy, in the northwest of France."


def test_json_parsing(caplog):
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content='```json {"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France."} ```',
        )
    ]

    base_generator = SimpleQuestionGenerator(llm_client=llm_client)
    with caplog.at_level(logging.DEBUG, logger="giskard.rag"):
        completion = base_generator._llm_complete(messages=[])

    assert isinstance(completion, dict)
    assert completion["question"] == "Where is Camembert from?"
    assert completion["answer"] == "Camembert was created in Normandy, in the northwest of France."

    assert "JSON decoding error" in caplog.text

    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content='```json {"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France." ```',
        ),
        LLMMessage(
            role="assistant",
            content='{"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France."}',
        ),
    ]

    base_generator = SimpleQuestionGenerator(llm_client=llm_client)
    with caplog.at_level(logging.DEBUG, logger="giskard.rag"):
        completion = base_generator._llm_complete(messages=[])

    assert isinstance(completion, dict)
    assert completion["question"] == "Where is Camembert from?"
    assert completion["answer"] == "Camembert was created in Normandy, in the northwest of France."

    assert "JSON decoding error" in caplog.text
