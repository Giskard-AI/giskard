from typing import Optional, Sequence, Union

import itertools

from ..utils.analytics_collector import analytics
from .knowledge_base import KnowledgeBase
from .question_generators import (
    QuestionGenerator,
    complex_questions,
    conversational_questions,
    distracting_questions,
    double_questions,
    simple_questions,
    situational_questions,
)
from .question_generators.utils import maybe_tqdm
from .testset import QATestset


def generate_testset(
    knowledge_base: KnowledgeBase,
    num_questions: Optional[int] = 120,
    question_generators: Optional[Union[QuestionGenerator, Sequence[QuestionGenerator]]] = None,
    language: Optional[str] = "en",
    agent_description: Optional[str] = "This agent is a chatbot that answers question from users.",
) -> QATestset:
    """Generate a testset from a knowledge base.

    Parameters
    ----------
    knowledge_base : KnowledgeBase
        The knowledge base to generate questions from.
    num_questions : int
        The number of questions to generate. By default 120.
    question_generators : Union[BaseQuestionModifier, Sequence[BaseQuestionModifier]]
        Question generators to use for question generation. If multiple generator are specified,
        `num_questions` will be generated with each generators. If not specified, all available question generators will be used.
    language : str, optional
        The language to use for question generation. The default is "en" to generate questions in english.
    agent_description : str, optional
        Description of the agent to be evaluated. This will be used in the prompt for question generation to get more fitting questions.

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

    # Ensure topics are computed and documents populated (@TODO: remove this)
    _ = knowledge_base.topics

    # Generate questions

    # @TODO: fix this ugly way to distribute the questions across generators
    generator_num_questions = [
        num_questions // len(question_generators) + (1 if i < num_questions % len(question_generators) else 0)
        for i in range(len(question_generators))
    ]

    main_generator = itertools.chain.from_iterable(
        [
            generator.generate_questions(
                knowledge_base,
                num_questions=n,
                agent_description=agent_description,
                language=language,
            )
            for generator, n in zip(question_generators, generator_num_questions)
        ]
    )

    questions = list(maybe_tqdm(main_generator, total=num_questions, desc="Generating questions"))

    for question in questions:
        topic_id = knowledge_base[question.metadata["seed_document_id"]].topic_id
        question.metadata["topic"] = knowledge_base.topics[topic_id]

    analytics.track(
        "raget:testset-generation",
        {
            "num_questions": num_questions,
            "language": language,
            "agent_description": agent_description,
            "question_generators": [qg.__class__.__name__ for qg in question_generators],
            "knowledge_base_size": len(knowledge_base._documents),
        },
    )
    return QATestset(questions)
