import uuid

from ..knowledge_base import KnowledgeBase
from .base import GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator
from .prompt import QAGenerationPrompt

OOS_PROMPT = """
You are a powerful auditor and mindful judger, your role is to generate question from a given context and 
by adding some fake or non-existing details/facts to the context to check whether the agent model you are auditing is capable of reasoning and answering questions
which has no direct answer in the provided context.

The agent model you are auditing is the following:
- Agent description: {agent_description}

All the generated content should be in the following language: {language}

There are your tasks, you should finish them step by step:
1. select one detail/fact from the context
2. add some fake details/facts which is not inclued in the whole provided context but based on the detail/facts you selected in the previous step.
3. Isolate this added fake detail/fact into a single sentence
4. Generate a question based on the new added isolated detail/fact, fit the question in the context and can not be answered by the information in the context.

The user will provide the context and give your answer after read it thoroughly.
You will return the isolated detail/fact and the question based exclusively on the new added isolated context.
You must output a single JSON object with keys 'selected fact', 'fake fact' and 'question' , without any other wrapping text or markdown and everything is in low letter. Make sure you only return valid JSON. 
"""

OOS_QUESTION_EXAMPLE_INPUT = """Paul Graham liked to buy a baguette every day at the local market.
Computers were expensive in those days and it took me years of nagging before I convinced my father to buy one, a TRS-80, in about 1980.
The gold standard then was the Apple II, but a TRS-80 was good enough."""

OOS_QUESTION_EXAMPLE_OUTPUT = """
{   
    "selected fact": "Paul Graham liked to buy a baguette every day at the local market.",
    "fake fact": "Paul Graham paid 1 USD for a baguette",
    "question": "How much did Paul pay for the baguette?"
}
"""

DUMMY_ANSWER = "This question can not be answered by the context. No sufficient information is provided in the context to answer this question."


class OutOfScopeGenerator(GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator):
    """
    Out of Knowledge Base question generator that generates questions from a KnowledgeBase.

    Parameters
    ----------
    context_neighbors: int, optional
        Number of context neighbors to use for question generation.
    context_similarity_threshold: float, optional
        Similarity threshold to keep neighboring document during question generation.
    context_window_length: int, optional
        Context window length of the llm used in the `llm_client` of the generator.
    llm_client: LLMClient, optional
        The LLM client to use for question generation. If not specified, a default openai client will be used.
    llm_temperature: float, optional
        The temperature to use in the LLM for question generation. The default is 0.5.
    """

    _OOKB_question_generation_prompt = QAGenerationPrompt(
        system_prompt=OOS_PROMPT,
        example_input=OOS_QUESTION_EXAMPLE_INPUT,
        example_output=OOS_QUESTION_EXAMPLE_OUTPUT,
    )

    _question_type = "out of scope"

    def generate_single_question(self, knowledge_base: KnowledgeBase, agent_description: str, language: str) -> dict:
        """
        Generate a question from a list of context documents.

        Parameters
        ----------
        knowledge_base: KnowledgeBase
            The knowledge base to generate the question from.
        agent_description: str
            The description of the agent to generate the question for.
        language: str
            The language to generate the question in.

        Returns
        -------
        Tuple[dict, dict]
            The generated question and the metadata of the question.
        """
        seed_document = knowledge_base.get_random_document()
        
        context_documents = knowledge_base.get_neighbors(
            seed_document, self._context_neighbors, self._context_similarity_threshold
        )

        reference_context = "\n\n".join([f"Document {doc.id}: {doc.content}" for doc in context_documents])

        # setup the OOKB question generation prompt
        question_messages = self._OOKB_question_generation_prompt.to_messages(
            system_prompt_input={"agent_description": agent_description, "language": language},
            user_input=seed_document.content,
        )

        generated_qa = self._llm_complete(messages=question_messages)

        question_metadata = {"question_type": self._question_type, "seed_document_id": seed_document.id}

        question = {
            "id": str(uuid.uuid4()),
            "question": generated_qa["question"],
            "reference_answer": DUMMY_ANSWER,
            "reference_context": reference_context,
            "conversation_history": [],
            "metadata": question_metadata,
        }

        return question

oos_questions = OutOfScopeGenerator()
