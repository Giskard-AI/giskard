from typing import Optional, Sequence, Union

import pandas as pd

from .knowledge_base import KnowledgeBase
from .question_generators import (
    BaseQuestionGenerator,
    complex_questions,
    conversational_questions,
    distracting_questions,
    double_questions,
    simple_questions,
    situational_questions,
)
from .testset import QATestset


def generate_testset(
    knowledge_base: KnowledgeBase,
    num_questions: int,
    question_generators: Optional[Union[BaseQuestionGenerator, Sequence[BaseQuestionGenerator]]] = None,
    language: Optional[str] = "en",
    assistant_description: Optional[str] = "This assistant is a chatbot that answers question from users.",
) -> QATestset:
    """Generate a testset from a knowledge base.
    By default it generates `num_questions` questions using the `giskard.rag.base_question_generator.BaseQuestionsGenerator`. If question modifiers are provided,
    it will generate `num_questions` questions using each of the modifiers as well.

    Parameters
    ----------
    knowledge_base : KnowledgeBase
        The knowledge base to generate questions from.
    num_questions : int
        The number of questions to generate. By default 30.
    question_generators : Union[BaseQuestionModifier, Sequence[BaseQuestionModifier]]
        Question generators to use for question generation. If multiple generator are specified,
        `num_questions` will be generated with each generators. If not specified, all available question generators will be used.
    language : str, optional
        The language to use for question generation. The default is "en" to generate questions in english.
    assistant_description : str, optional
        Description of the assistant to be evaluated. This will be used in the prompt for question generation to get more fitting questions.
    Returns
    -------
    QATestset
        The generated test set.
    """
    if question_generators is None:
        question_generators = [
            simple_questions,
            complex_questions,
            distracting_questions,
            situational_questions,
            double_questions,
            conversational_questions,
        ]

    if not isinstance(question_generators, Sequence):
        question_generators = [question_generators]

    questions = []
    for generator in question_generators:
        questions.extend(generator._generate_questions(knowledge_base, num_questions, assistant_description, language))

    for question in questions:
        topic_id = knowledge_base.get_document(question["metadata"]["seed_document_id"]).topic_id
        question["metadata"]["topic"] = knowledge_base.topics[topic_id]
    return QATestset(pd.DataFrame(questions).set_index("id"))
