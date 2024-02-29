from enum import Enum


class QuestionTypes(int, Enum):
    EASY = 1
    COMPLEX = 2
    DISTRACTING_ELEMENT = 3
    SITUATIONAL = 4
    DOUBLE_QUESTION = 5
    CONVERSATIONAL = 6
    MULTI_CONTEXT = 7
    OUT_OF_SCOPE = 8


class RAGComponents(int, Enum):
    GENERATOR = 1
    RETRIEVER = 2
    REWRITER = 3
    ROUTING = 4
    KNOWLEDGE_BASE = 5


QUESTION_ATTRIBUTION = {
    RAGComponents.GENERATOR: [
        QuestionTypes.EASY,
        QuestionTypes.COMPLEX,
        QuestionTypes.DISTRACTING_ELEMENT,
        QuestionTypes.SITUATIONAL,
    ],
    RAGComponents.RETRIEVER: [QuestionTypes.EASY, QuestionTypes.DISTRACTING_ELEMENT, QuestionTypes.MULTI_CONTEXT],
    RAGComponents.REWRITER: [
        QuestionTypes.DISTRACTING_ELEMENT,
        QuestionTypes.DOUBLE_QUESTION,
        QuestionTypes.CONVERSATIONAL,
        QuestionTypes.MULTI_CONTEXT,
    ],
    RAGComponents.ROUTING: [QuestionTypes.EASY, QuestionTypes.OUT_OF_SCOPE],
    RAGComponents.KNOWLEDGE_BASE: [QuestionTypes.OUT_OF_SCOPE],
}
