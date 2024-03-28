from typing import Sequence

from ..llm.client.base import ChatMessage, LLMClient

RECOMMENDATION_SYSTEM_PROMPT = """You are an expert at designing Retrieval Augmented Generation (RAG) systems. You new task is to help debug a RAG based on several scores.

The RAG is composed of the following components:
- Knowledge base: contains all the documents and information the RAG has access to.
- Retriever: an algorithm that find relevant documents in the knowledge base, given a user's question.
- Generator: a LLM model that generates the answers to the user's questions.
- Rewriter: rewrites the user questions to match better with the use case or the knowledge base.
- Router: a filter that decides which component to use to answer the user's question. It can also be a moderation layer.

The RAG has been evaluated on a set of questions. The questions are of various types:
- Simple questions: questions that can be answered with a single document. (Evaluated components: Generator, Retriever, Router)
- Complex questions: questions more difficult to answer due to paraphrasing. (Evaluated components: Generator)
- Distracting questions: questions which include random information from the knowledge base. (Evaluated components: Generator, Retriever, Rewriter)
- Situational questions: questions that includes situational context given by a user. (Evaluated components: Generator)
- Conversational questions: questions that are part of a conversation. (Evaluated components: Rewriter)
- Double questions: questions that include two questions. (Evaluated components: Rewriter)

While the knowledge base quality is not assessed by any question type, each question is related to exactly one of these topics. 
A proxy for the quality of the knowledge base is the RAG's ability to answer equally well across all topics. Here are the topics:
{topics}

Your are now provided with the scores of the agent on each question type and each topic.
"""

RECOMMENDATION_USER_PROMPT = """
Scores per question type:
{scores_per_question_type}

Scores per topic:
{scores_per_topic}

Give me a short recommendation including the most important action I should take to improve my RAG system.
Your answer should be at most 2 sentences long.
"""


def get_rag_recommendation(
    topics: Sequence[str], scores_per_question_type: dict, scores_per_topic: dict, llm_client: LLMClient
):
    formatted_topics = "\n".join([f"- {topic}" for idx, topic in enumerate(topics)])
    formatted_scores_per_question_type = "\n".join(
        [f"- {question_type}: {score}" for question_type, score in scores_per_question_type.items()]
    )
    formatted_scores_per_topic = "\n".join([f"- {topic}: {score}" for topic, score in scores_per_topic.items()])

    recommendation = llm_client.complete(
        [
            ChatMessage(role="system", content=RECOMMENDATION_SYSTEM_PROMPT.format(topics=formatted_topics)),
            ChatMessage(
                role="user",
                content=RECOMMENDATION_USER_PROMPT.format(
                    scores_per_question_type=formatted_scores_per_question_type,
                    scores_per_topic=formatted_scores_per_topic,
                ),
            ),
        ]
    )
    return recommendation.content
