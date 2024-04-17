import logging
from unittest.mock import MagicMock, Mock

from giskard.rag import QuestionSample
from giskard.rag.question_generators import SimpleQuestionsGenerator
from giskard.rag.testset_generation import generate_testset

q1 = QuestionSample(
    id="test1",
    question="Where is Camembert from?",
    reference_answer="Camembert was created in Normandy, in the northwest of France.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={"seed_document_id": "1", "question_type": "simple"},
)
q2 = QuestionSample(
    id="test2",
    question="What is freeriding ski?",
    reference_answer="Freeriding is a style of snowboarding or skiing.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={"seed_document_id": "0", "question_type": "simple"},
)
q3 = QuestionSample(
    id="test3",
    question="Where is Camembert from?",
    reference_answer="Camembert was created in Normandy, in the northwest of France.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={"seed_document_id": "1", "question_type": "complex"},
)
q4 = QuestionSample(
    id="test4",
    question="What is freeriding ski?",
    reference_answer="Freeriding is a style of snowboarding or skiing.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={
        "seed_document_id": "0",
        "question_type": "distracting element",
        "distracting_context": "Distracting content",
    },
)
q5 = QuestionSample(
    id="test5",
    question="Where is Camembert from?",
    reference_answer="Camembert was created in Normandy, in the northwest of France.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={
        "seed_document_id": "1",
        "question_type": "situational",
        "situational_context": "I am a cheese enthusiast and I want to know more about Camembert.",
    },
)
q6 = QuestionSample(
    id="test6",
    question="What is freeriding ski?",
    reference_answer="Freeriding is a style of snowboarding or skiing.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[],
    metadata={
        "seed_document_id": "0",
        "question_type": "double",
        "original_questions": [
            {"question": "Where is Camembert from?", "answer": "Normandy"},
            {"question": "Where is Scamorza from?", "answer": "Southern Italy"},
        ],
    },
)
q7 = QuestionSample(
    id="test7",
    question="What is freeriding ski?",
    reference_answer="Freeriding is a style of snowboarding or skiing.",
    reference_context="Document 1: Camembert was created in Normandy, in the northwest of France.",
    conversation_history=[
        {"role": "user", "content": "First message."},
        {"role": "assistant", "content": "First response."},
    ],
    metadata={"seed_document_id": "0", "question_type": "conversational"},
)


def test_testset_generation():
    knowledge_base = MagicMock()
    knowledge_base._document_index = {"0": Mock(topic_id=0), "1": Mock(topic_id=1)}
    knowledge_base.__getitem__ = lambda obj, idx: getattr(obj, "_document_index")[idx]
    knowledge_base.topics = ["Cheese", "Ski"]

    question_generator = Mock()
    question_generator.generate_questions.return_value = [q1, q2]

    test_set = generate_testset(
        knowledge_base=knowledge_base,
        num_questions=2,
        question_generators=question_generator,
    )

    assert len(test_set) == 2

    assert test_set.samples[0].question == q1.question
    assert test_set.samples[0].reference_answer == q1.reference_answer
    assert test_set.samples[0].metadata == {
        "seed_document_id": "1",
        "topic": "Ski",
        "question_type": "simple",
    }

    assert test_set.samples[1].question == q2.question
    assert test_set.samples[1].reference_answer == q2.reference_answer
    assert test_set.samples[1].metadata == {
        "seed_document_id": "0",
        "topic": "Cheese",
        "question_type": "simple",
    }


def test_testset_question_types():
    knowledge_base = Mock()
    documents = [Mock(topic_id=1)] + [Mock(topic_id=0)] * 6
    knowledge_base._documents = documents
    knowledge_base.__getitem__ = lambda obj, idx: documents[0]
    knowledge_base.topics = ["Cheese", "Ski"]

    simple_gen = Mock()
    simple_gen.generate_questions.return_value = [q1, q2]
    complex_gen = Mock()
    complex_gen.generate_questions.return_value = [q3]
    distracting_gen = Mock()
    distracting_gen.generate_questions.return_value = [q4]
    situational_gen = Mock()
    situational_gen.generate_questions.return_value = [q5]
    double_gen = Mock()
    double_gen.generate_questions.return_value = [q6]
    conversational_gen = Mock()
    conversational_gen.generate_questions.return_value = [q7]

    question_generators = [simple_gen, complex_gen, distracting_gen, situational_gen, double_gen, conversational_gen]

    testset = generate_testset(knowledge_base=knowledge_base, num_questions=7, question_generators=question_generators)
    assert len(testset.samples) == 7
    assert testset.samples[0].metadata["question_type"] == "simple"
    assert testset.samples[1].metadata["question_type"] == "simple"
    assert testset.samples[2].metadata["question_type"] == "complex"
    assert testset.samples[3].metadata["question_type"] == "distracting element"
    assert testset.samples[4].metadata["question_type"] == "situational"
    assert testset.samples[5].metadata["question_type"] == "double"
    assert testset.samples[6].metadata["question_type"] == "conversational"

    for idx, row_id in enumerate(testset.to_pandas().index):
        if testset._dataframe.metadata[row_id]["question_type"] != "conversational":
            assert testset._dataframe.conversation_history[row_id] == []
        else:
            assert testset._dataframe["conversation_history"][row_id] == [
                {"role": "user", "content": "First message."},
                {"role": "assistant", "content": "First response."},
            ]

    assert "distracting_context" in testset._dataframe["metadata"][3]
    assert testset._dataframe["metadata"][3]["distracting_context"] == "Distracting content"

    assert "situational_context" in testset._dataframe["metadata"][4]
    assert (
        testset._dataframe["metadata"][4]["situational_context"]
        == "I am a cheese enthusiast and I want to know more about Camembert."
    )
    assert testset._dataframe["metadata"][5]["original_questions"] == [
        {"question": "Where is Camembert from?", "answer": "Normandy"},
        {"question": "Where is Scamorza from?", "answer": "Southern Italy"},
    ]


def test_question_generation_fail(caplog):
    knowledge_base = Mock()
    documents = [Mock(topic_id=1)] + [Mock(topic_id=0)] * 6
    knowledge_base._documents = documents
    knowledge_base.__getitem__ = lambda obj, idx: documents[0]
    knowledge_base.topics = ["Cheese", "Ski"]

    simple_gen = Mock()
    simple_gen.generate_questions.return_value = [q1, q2]
    failing_gen = SimpleQuestionsGenerator(llm_client=Mock())

    with caplog.at_level(logging.DEBUG, logger="giskard.rag"):
        testset = generate_testset(
            knowledge_base=knowledge_base,
            num_questions=4,
            question_generators=[simple_gen, failing_gen],
        )
    assert len(testset.to_pandas()) == 2
    assert "Encountered error in question generation" in caplog.text
