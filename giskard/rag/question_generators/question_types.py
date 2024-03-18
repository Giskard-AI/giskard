from enum import Enum


class RAGComponents(int, Enum):
    GENERATOR = 1
    RETRIEVER = 2
    REWRITER = 3
    ROUTING = 4
    KNOWLEDGE_BASE = 5


QUESTION_ATTRIBUTION = {
    RAGComponents.GENERATOR: [
        "simple",
        "complex",
        "distracting element",
        "situational",
        "double",
    ],
    RAGComponents.RETRIEVER: ["simple", "distracting element", "multi-context"],
    RAGComponents.REWRITER: [
        "distracting element",
        "double",
        "conversational",
        "multi-context",
    ],
    RAGComponents.ROUTING: ["simple", "out of scope"],
    RAGComponents.KNOWLEDGE_BASE: ["out of scope"],
}
