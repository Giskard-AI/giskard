import uuid

from ..knowledge_base import KnowledgeBase
from .base import GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator
from .prompt import QAGenerationPrompt

OOKB_PROMPT = """
You are a powerful auditor and mindful judger, your role is to generate question from a given context and 
by adding some fake or non-existing details/facts to the context to check whether the agent model you are auditing is capable of reasoning and answering questions
which has no direct answer in the provided context.

There are your tasks, you should finish them step by step:
0. select one detail/fact from the context
1. add some fake details/facts which is not inclued in the whole provided context but based on the detail/facts you selected in the previous step.
2. Isolate this added fake detail/fact into a single sentence
3. Generate a question based on the new added isolated detail/fact, fit the question in the context and can not be answered by the information in the context.

The user will provide the context and give your answer after read it thoroughly.
You will return the isolated detail/fact and the question based exclusively on the new added isolated context.
You must output a single JSON object with keys 'selected detail/fact', 'fake detail/fact' and 'question' , without any other wrapping text or markdown and everything is in low letter. Make sure you only return valid JSON. 
"""

OOKB_QUESTION_EXAMPLE_INPUT = """Paul Graham liked to buy a baguette every day at the local market."""

OOKB_QUESTION_EXAMPLE_OUTPUT = """
{   
    "selected detail/fact": "Paul Graham liked to buy a baguette every day at the local market.",
    "fake detail/fact": "Paul Graham paid 1 USD for a baguette",
    "question": "How much did Paul pay for the baguette?"
}
"""

QUESTION_CHECK_PROMPT = """
You are a powerful auditor and mindful juder, your role is to check whether the input question can be answered by the context and the related context documents or not.

The agent model you are auditing is the following:
- Agent description: {agent_description}

Your task is to check if the given question can be answered by the context and the related context or not. 
In case the question is asking some facts in the context, unless the facts are explicitly mentioned in the context, the question can not be answered by the context.

All the generated content should be in the following language: {language}

Think step by step and consider the context in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
If the question can be answered by the context, return True along with the reason. If the question can not be answered by the context, return False along with the reason.
You must output a single JSON object with keys 'can_be_answered' and 'correctness_reason'. NO ANY MARKDOWN STRING. Make sure you return a valid JSON object.
"""

QUESTION_FILTER_INPUT_TEMPLATE = """
<question>
{question}
</question>

<context>
{context}
</context>

<related_context>
{related_context}
</related_context>
"""

QUESTION_FILTER_INPUT_EXAMPLE = QUESTION_FILTER_INPUT_TEMPLATE.format(
    question="What was the name of the Boston investment bank where Jessica worked?",
    context="Jessica was in charge of marketing at a Boston investment bank.",
    related_context="Jessica was in charge of marketing at a Boston investment bank. This bank thought it understood startups, but over the next year, as she met friends of mine from the startup world, she was surprised how different reality was. And how colorful their stories were. So she decided to compile a book of interviews with startup founders.",
)

QUESTION_FILTER_OUTPUT_EXAMPLE = """{
    "can_be_answered": false,
    "correctness_reason": "The name of the Boston investment bank where Jessica worked is not directly mentioned in the context."
}
"""

DUMMY_ANSWER = "This question can not be answered by the context. No sufficient information is provided in the context to answer this question."


class OutOfKnowledgeBaseGenerator(GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator):
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
        system_prompt=OOKB_PROMPT,
        example_input=OOKB_QUESTION_EXAMPLE_INPUT,
        example_output=OOKB_QUESTION_EXAMPLE_OUTPUT,
    )

    _OOKB_question_check_prompt = QAGenerationPrompt(
        system_prompt=QUESTION_CHECK_PROMPT,
        user_input_template=QUESTION_FILTER_INPUT_TEMPLATE,
        example_input=QUESTION_FILTER_INPUT_EXAMPLE,
        example_output=QUESTION_FILTER_OUTPUT_EXAMPLE,
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
        context_str = "\n------\n".join(["", *[doc.content for doc in context_documents], ""])

        reference_context = "\n\n".join([f"Document {doc.id}: {doc.content}" for doc in context_documents])

        for _ in range(3):
            # setup the OOKB question generation prompt
            question_messages = self._OOKB_question_generation_prompt.to_messages(
                system_prompt_input={"agent_description": agent_description, "language": language},
                user_input=seed_document.content,
            )

            generated_qa = self._llm_complete(messages=question_messages)

            # check the generated question
            check_messages = self._OOKB_question_check_prompt.to_messages(
                system_prompt_input={"agent_description": agent_description, "language": language},
                user_input=dict(
                    question=generated_qa["question"], context=seed_document.content, related_context=context_str
                ),
            )

            check_result = self._llm_complete(messages=check_messages)

            if bool(check_result["can_be_answered"]):
                continue

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

        raise Exception("Can not generate a question that can not be answered by the context after 3 attempts.")


ookb_questions = OutOfKnowledgeBaseGenerator()
