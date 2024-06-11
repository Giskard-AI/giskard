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
    RAGComponents.ROUTING: ["out of scope"],
    RAGComponents.KNOWLEDGE_BASE: ["out of scope"],
}

COMPONENT_DESCRIPTIONS = {
    "GENERATOR": "The Generator is the LLM inside the RAG to generate the answers.",
    "RETRIEVER": "The Retriever fetches relevant documents from the knowledge base according to a user query.",
    "REWRITER": "The Rewriter modifies the user query to match a predefined format or to include the context from the chat history.",
    "ROUTING": "The Router filters the query of the user based on his intentions (intentions detection).",
    "KNOWLEDGE_BASE": "The knowledge base is the set of documents given to the RAG to generate the answers. Its scores is computed differently from the other components: it is the difference between the maximum and minimum correctness score across all the topics of the knowledge base.",
}
