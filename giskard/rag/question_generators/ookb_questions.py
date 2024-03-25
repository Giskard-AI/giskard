import uuid

from ..knowledge_base import KnowledgeBase
from .base import _LLMBasedQuestionGenerator, GenerateFromSingleQuestionMixin
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionsGenerator

OoKB_PROMPT = """
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

OoKB_QUESTION_EXAMPLE_INPUT = """Paul Graham liked to buy a baguette every day at the local market."""

OoKB_QUESTION_EXAMPLE_OUTPUT = """

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
    question = "What was the name of the Boston investment bank where Jessica worked?", 
    context = "Jessica was in charge of marketing at a Boston investment bank.",
    related_context = "[11]\n\nIn the print era, the channel for publishing essays had been vanishingly small. Except for a few officially anointed thinkers who went to the right parties in New York, the only people allowed to publish essays were specialists writing about their specialties. There were so many essays that had never been written, because there had been no way to publish them. Now they could be, and I was going to write them. [12]\n\nI've worked on several different things, but to the extent there was a turning point where I figured out what to work on, it was when I started publishing essays online. From then on I knew that whatever else I did, I'd always write essays too.\n\nI knew that online essays would be a marginal medium at first. Socially they'd seem more like rants posted by nutjobs on their GeoCities sites than the genteel and beautifully typeset compositions published in The New Yorker. But by this point I knew enough to find that encouraging instead of discouraging.\n\nOne of the most conspicuous patterns I've noticed in my life is how well it has worked, for me at least, to work on things that weren't prestigious. Still life has always been the least prestigious form of painting. Viaweb and Y Combinator both seemed lame when we started them. I still get the glassy eye from strangers when they ask what I'm writing, and I explain that it's an essay I'm going to publish on my web site. Even Lisp, though prestigious intellectually in something like the way Latin is, also seems about as hip.\n\nIt's not that unprestigious types of work are good per se. But when you find yourself drawn to some kind of work despite its current lack of prestige, it's a sign both that there's something real to be discovered there, and that you have the right kind of motives. Impure motives are a big danger for the ambitious. If anything is going to lead you astray, it will be the desire to impress people. So while working on things that aren't prestigious doesn't guarantee you're on the right track, it at least guarantees you're not on the most common type of wrong one.\n\nOver the next several years I wrote lots of essays about all kinds of different topics. O'Reilly reprinted a collection of them as a book, called Hackers & Painters after one of the essays in it. I also worked on spam filters, and did some more painting. I used to have dinners for a group of friends every thursday night, which taught me how to cook for groups. And I bought another building in Cambridge, a former candy factory (and later, twas said, porn studio), to use as an office.\n\nOne night in October 2003 there was a big party at my house. It was a clever idea of my friend Maria Daniels, who was one of the thursday diners. Three separate hosts would all invite their friends to one party. So for every guest, two thirds of the other guests would be people they didn't know but would probably like. One of the guests was someone I didn't know but would turn out to like a lot: a woman called Jessica Livingston. A couple days later I asked her out.\n\nJessica was in charge of marketing at a Boston investment bank. This bank thought it understood startups, but over the next year, as she met friends of mine from the startup world, she was surprised how different reality was. And how colorful their stories were. So she decided to compile a book of interviews with startup founders.\n\nWhen the bank had financial problems and she had to fire half her staff, she started looking for a new job. In early 2005 she interviewed for a marketing job at a Boston VC firm. It took them weeks to make up their minds, and during this time I started telling her about all the things that needed to be fixed about venture capital. They should make a larger number of smaller investments instead of a handful of giant ones, they should be funding younger, more technical founders instead of MBAs, they should let the founders remain as CEO, and so on.\n\nOne of my tricks for writing essays had always been to give talks. The prospect of having to stand up in front of a group of people and tell them something that won't waste their time is a great spur to the imagination. When the Harvard Computer Society, the undergrad computer club, asked me to give a talk, I decided I would tell them how to start a startup. Maybe they'd be able to avoid the worst of the mistakes we'd made.")

QUESTION_FILTER_OUTPUT_EXAMPLE = """

{
    "can_be_answered": false,
    "correctness_reason": "The name of the Boston investment bank where Jessica worked is not directly mentioned in the context."
}

"""

DUMMY_ANSWER = "This question can not be answered by the context. No sufficient information is provided in the context to answer this question."


class OutofKnowledgeBaseGenerator(GenerateFromSingleQuestionMixin, _LLMBasedQuestionGenerator):
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

    _OoKB_question_generation_prompt = QAGenerationPrompt(
        system_prompt=OoKB_PROMPT,
        example_input=OoKB_QUESTION_EXAMPLE_INPUT,
        example_output=OoKB_QUESTION_EXAMPLE_OUTPUT,
    )

    _OoKB_question_check_prompt = QAGenerationPrompt(
        system_prompt=QUESTION_CHECK_PROMPT,
        user_input_template=QUESTION_FILTER_INPUT_TEMPLATE,
        example_input=QUESTION_FILTER_INPUT_EXAMPLE,
        example_output=QUESTION_FILTER_OUTPUT_EXAMPLE
    )

    _question_type = "out of scope"

    # TODO: split the following function into two parts,

    # 1. generate one single question by using OoKB_PROMPT with example input and output
    # 2. check the question by using QUESTION_FILTER_INPUT_TEMPLATE with example input and output
    # 3. if the question can not be answered by the context, return the Question Object with the DUMMY_ANSWER
    # 4. if the question can be answered by the context, back to step 1 and generate a new question and check it again until the question can not be answered by the context.

    def generate_single_question(self, knowledge_base: KnowledgeBase, agent_description: str, language: str) -> dict:
        """
        Generate a question from a list of context documents.

        Parameters
        ----------
        context_documents : Sequence[Document]
            The context documents to generate the question from.

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

        # 3 attempts to generate a question that can not be answered by the context
        for _ in range(3):
            # setup the ookb question generation prompt
            question_messages = self._OoKB_question_generation_prompt.to_messages(
                system_prompt_input={"agent_description": agent_description, "language": language},
                user_input=seed_document.content,
            )

            generated_qa = self._llm_complete(messages=question_messages)

            # check the generated question
            check_messages = self._OoKB_question_check_prompt.to_messages(
                system_prompt_input={"agent_description": agent_description, "language": language},
                user_input=dict(question=generated_qa["question"], context=seed_document.content, related_context=context_str)
            )

            check_result = self._llm_complete(messages=check_messages)

            if not check_result["can_be_answered"]:
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

OoKB_questions = OutofKnowledgeBaseGenerator()
