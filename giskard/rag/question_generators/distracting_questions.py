from ..knowledge_base import KnowledgeBase
from ..testset import QuestionSample
from .base import _BaseModifierGenerator
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionsGenerator

DISTRACTING_SYSTEM_PROMPT = """You are an expert at rewriting questions.
Your task is to re-write questions that will be used to evaluate the following agent:
- Agent description: {agent_description}  

Your task is to complexify questions given a provided context. 
Please respect the following rules to generate the question:
- The new question must include a condition or constraint based on the provided context. 
- The original question direction should be preserved.
- The question must be plausible according to the context and the agent description.
- The question must be self-contained and understandable by humans. 
- The question must be in this language: {language}

You will be provided the question delimited with <question></question> tags.
You will also be provided a context paragraph delimited with <context></context> tags.
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

DISTRACTING_INPUT_TEMPLATE = """<question>
{question}
</question>
<answer>
{answer}
</answer>
<context>
{context}
</context>"""

DISTRACTING_EXAMPLE_INPUT = DISTRACTING_INPUT_TEMPLATE.format(
    question="What job offer do you have for engineering student?",
    answer="We have plenty of different jobs for engineering student depending on your speciality: mechanical engineer, data scientist, electronic designer and many more.",
    context="Sometimes employers assume being accessible and inclusive only means providing physical access like ramps, accessible bathrooms and automatic opening doors. However, there are many other important ways to demonstrate that you welcome and want to attract a diverse workforce including people with disability.",
)

DISTRACTING_EXAMPLE_OUTPUT = """{
    "question": "Do you have any job opening suitable for engineering students with a disability? "
}"""


class DistractingQuestionsGenerator(_BaseModifierGenerator):
    _base_generator = SimpleQuestionsGenerator()

    _prompt = QAGenerationPrompt(
        system_prompt=DISTRACTING_SYSTEM_PROMPT,
        example_input=DISTRACTING_EXAMPLE_INPUT,
        example_output=DISTRACTING_EXAMPLE_OUTPUT,
        user_input_template=DISTRACTING_INPUT_TEMPLATE,
    )

    _question_type = "distracting element"

    def _modify_question(
        self, question: QuestionSample, knowledge_base: KnowledgeBase, agent_description: str, language: str
    ) -> QuestionSample:
        distracting_context = knowledge_base.get_random_document().content
        messages = self._prompt.to_messages(
            system_prompt_input={
                "agent_description": agent_description,
                "language": language,
            },
            user_input={
                "question": question.question,
                "answer": question.reference_answer,
                "context": distracting_context,
            },
        )
        question.metadata["question_type"] = self._question_type
        question.metadata["distracting_context"] = distracting_context
        out = self._llm_complete(messages=messages)
        question.question = out["question"]
        return question


distracting_questions = DistractingQuestionsGenerator()
