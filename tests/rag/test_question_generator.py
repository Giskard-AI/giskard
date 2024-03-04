from unittest.mock import Mock

from giskard.llm.client import LLMMessage
from giskard.rag.knowledge_base import Document
from giskard.rag.question_generators import SimpleQuestionsGenerator


def test_simple_question_generation():
    knowledge_base = Mock()
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content='{"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France."}',
        )
    ]

    question_generator = SimpleQuestionsGenerator(knowledge_base, llm_client=llm_client)

    documents = [
        Document(dict(content="Camembert is a cheese from Normandy, in the northwest of France.")),
        Document(dict(content="Cheese is made of milk.")),
        Document(dict(content="Milk is produced by cows, goats or sheep.")),
    ]

    qa, metadata = question_generator.generate_question(documents)

    assert qa["question"] == "Where is Camembert from?"
    assert qa["answer"] == "Camembert was created in Normandy, in the northwest of France."
    assert metadata["question_type"] == 1
    assert metadata["reference_context"] == "\n------\n".join(["", *[doc.content for doc in documents], ""])
