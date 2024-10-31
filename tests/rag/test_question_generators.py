import uuid
from unittest.mock import Mock, patch

from giskard.llm.client import ChatMessage
from giskard.rag.knowledge_base import Document
from giskard.rag.question_generators import (
    ComplexQuestionsGenerator,
    ConversationalQuestionsGenerator,
    DistractingQuestionsGenerator,
    DoubleQuestionsGenerator,
    OutOfScopeGenerator,
    SimpleQuestionsGenerator,
    SituationalQuestionsGenerator,
)
from giskard.rag.testset import QuestionSample

TEST_UUIDS = ["{}".format(i + 1) for i in range(6)]


def test_simple_question_generation():
    knowledge_base = Mock()
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"question": "Where is Camembert from?", "answer": "Camembert was created in Normandy, in the northwest of France."}',
        )
    ]
    with patch.object(uuid, "uuid4", side_effect=TEST_UUIDS):
        documents = [
            Document(dict(content="Camembert is a cheese from Normandy, in the northwest of France.")),
            Document(dict(content="Cheese is made of milk.")),
            Document(dict(content="Milk is produced by cows, goats or sheep.")),
        ]
    knowledge_base.get_random_document = Mock(return_value=documents[0])
    knowledge_base.get_random_documents = Mock(return_value=documents)
    knowledge_base.get_neighbors = Mock(return_value=documents)

    question_generator = SimpleQuestionsGenerator(llm_client=llm_client)

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "Where is Camembert from?"
    assert isinstance(question.id, str)
    assert question.reference_answer == "Camembert was created in Normandy, in the northwest of France."
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "simple"
    assert question.metadata["seed_document_id"] == "1"


def test_complex_question_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"question": "Among all regions of France which one is the home of Camembert?"}',
        )
    ]
    knowledge_base = Mock()

    question_generator = ComplexQuestionsGenerator(llm_client=llm_client)
    question_generator._base_generator = Mock()
    question_generator._base_generator.generate_questions = Mock(
        return_value=[
            QuestionSample(
                question="Where is Camembert from?",
                id="1",
                reference_answer="Camembert was created in Normandy, in the northwest of France.",
                reference_context="Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep.",
                conversation_history=[],
                metadata={"question_type": "simple", "seed_document_id": "2"},
            )
        ]
    )

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "Among all regions of France which one is the home of Camembert?"
    assert isinstance(question.id, str)
    assert question.reference_answer == "Camembert was created in Normandy, in the northwest of France."
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "complex"
    assert question.metadata["seed_document_id"] == "2"


def test_distracting_question_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"question": "Scamorza is a cheese from Italy, but where is the camembert from?"}',
        )
    ]
    knowledge_base = Mock()
    knowledge_base.get_random_document = Mock(
        return_value=Document(dict(content="Scamorza is a cheese from southern Italy."))
    )

    question_generator = DistractingQuestionsGenerator(llm_client=llm_client)
    question_generator._base_generator = Mock()
    question_generator._base_generator.generate_questions = Mock(
        return_value=[
            QuestionSample(
                question="Where is Camembert from?",
                id="1",
                reference_answer="Camembert was created in Normandy, in the northwest of France.",
                reference_context="Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep.",
                conversation_history=[],
                metadata={"question_type": "simple", "seed_document_id": "2"},
            )
        ]
    )

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "Scamorza is a cheese from Italy, but where is the camembert from?"
    assert isinstance(question.id, str)
    assert question.reference_answer == "Camembert was created in Normandy, in the northwest of France."
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "distracting element"
    assert question.metadata["seed_document_id"] == "2"
    assert question.metadata["distracting_context"] == "Scamorza is a cheese from southern Italy."


def test_situational_question_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content="A cheese enthusiast is asking various questions about cheese.",
        ),
        ChatMessage(
            role="assistant",
            content='{"question": "I really love cheese, I wonder where is the camembert from?"}',
        ),
    ]
    knowledge_base = Mock()

    question_generator = SituationalQuestionsGenerator(llm_client=llm_client)
    question_generator._base_generator = Mock()
    question_generator._base_generator.generate_questions = Mock(
        return_value=[
            QuestionSample(
                question="Where is Camembert from?",
                id="1",
                reference_answer="Camembert was created in Normandy, in the northwest of France.",
                reference_context="Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep.",
                conversation_history=[],
                metadata={"question_type": "simple", "seed_document_id": "2"},
            )
        ]
    )

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "I really love cheese, I wonder where is the camembert from?"
    assert isinstance(question.id, str)
    assert question.reference_answer == "Camembert was created in Normandy, in the northwest of France."
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "situational"
    assert question.metadata["seed_document_id"] == "2"


def test_double_question_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='[{"question": "Where is scamorza from?", "answer": "Scamorza is a cheese from southern Italy."}, {"question": "Where is scamorza camembert from?", "answer": "Camembert is a cheese from Normandy."}]',
        ),
        ChatMessage(
            role="assistant",
            content='{"question": "Where are scamorza and camembert from?", "answer": "Scamorza is a cheese from southern Italy, but Camembert was created in Normandy, in the northwest of France."}',
        ),
    ]
    knowledge_base = Mock()
    with patch.object(uuid, "uuid4", side_effect=TEST_UUIDS):
        documents = [
            Document(dict(content="Camembert is a cheese from Normandy, in the northwest of France.")),
            Document(dict(content="Cheese is made of milk.")),
            Document(dict(content="Milk is produced by cows, goats or sheep.")),
        ]
    knowledge_base.get_random_document = Mock(return_value=documents[0])
    knowledge_base.get_random_documents = Mock(return_value=documents)
    knowledge_base.get_neighbors = Mock(return_value=documents)

    question_generator = DoubleQuestionsGenerator(llm_client=llm_client)

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "Where are scamorza and camembert from?"
    assert isinstance(question.id, str)
    assert (
        question.reference_answer
        == "Scamorza is a cheese from southern Italy, but Camembert was created in Normandy, in the northwest of France."
    )
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "double"
    assert question.metadata["seed_document_id"] == "1"


def test_conversational_question_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"question": "Where is it from?", "introduction": "I would like to know some information about the Camembert."}',
        )
    ]
    knowledge_base = Mock()

    question_generator = ConversationalQuestionsGenerator(llm_client=llm_client)
    question_generator._base_generator.generate_questions = Mock(
        return_value=[
            QuestionSample(
                question="Where is Camembert from?",
                id="1",
                reference_answer="Camembert was created in Normandy, in the northwest of France.",
                reference_context="Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep.",
                conversation_history=[],
                metadata={"question_type": "simple", "seed_document_id": "2"},
            )
        ]
    )

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "Where is it from?"
    assert isinstance(question.id, str)
    assert question.reference_answer == "Camembert was created in Normandy, in the northwest of France."
    assert (
        question.reference_context
        == "Document 1: Camembert is a cheese from Normandy, in the northwest of France.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == [
        {"role": "user", "content": "I would like to know some information about the Camembert."},
        {"role": "assistant", "content": "How can I help you with that?"},
    ]

    assert question.metadata["question_type"] == "conversational"
    assert question.metadata["seed_document_id"] == "2"


def test_oos_question_generation():
    knowledge_base = Mock()
    llm_client = Mock()

    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"selected_fact": "Paul Graham liked to buy a baguette every day at the local market.", "fake_fact": "Paul Graham paid 1 USD for a baguette", "question": "How much did Paul pay for the baguette?"}',
        )
    ]

    documents = [
        Document(dict(content="Paul Graham liked to buy a baguette every day at the local market."), doc_id="1"),
        Document(dict(content="Cheese is made of milk."), doc_id="2"),
        Document(dict(content="Milk is produced by cows, goats or sheep."), doc_id="3"),
    ]
    knowledge_base.get_random_document = Mock(
        return_value=Document(
            dict(content="Paul Graham liked to buy a baguette every day at the local market."), doc_id="1"
        )
    )
    knowledge_base.get_random_documents = Mock(return_value=documents)
    knowledge_base.get_neighbors = Mock(return_value=documents)

    question_generator = OutOfScopeGenerator(llm_client=llm_client)

    question = list(
        question_generator.generate_questions(
            knowledge_base=knowledge_base, num_questions=1, agent_description="Test", language="en"
        )
    )[0]

    assert question.question == "How much did Paul pay for the baguette?"
    assert isinstance(question.id, str)
    assert (
        question.reference_answer
        == "This question can not be answered by the context. No sufficient information is provided in the context to answer this question."
    )
    assert (
        question.reference_context
        == "Document 1: Paul Graham liked to buy a baguette every day at the local market.\n\nDocument 2: Cheese is made of milk.\n\nDocument 3: Milk is produced by cows, goats or sheep."
    )
    assert question.conversation_history == []
    assert question.metadata["question_type"] == "out of scope"
    assert question.metadata["seed_document_id"] == "1"
