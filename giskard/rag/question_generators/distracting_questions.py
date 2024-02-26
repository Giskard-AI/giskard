from typing import Sequence

from ..vector_store import Document
from .prompt import QAGenerationPrompt
from .simple_questions import SimpleQuestionGenerator
from .utils import DifficultyLevel

DISTRACTING_SYSTEM_PROMPT = """You are an expert at rewriting questions.
Your task is to re-write questions that will be used to evaluate the following assistant:
- Assistant description: {assistant_description}  

Your task is to complexify questions given a provided context. 
Please respect the following rules to generate the question:
- The new question must include a condition or constraint based on the provided context. 
- The original question direction should be preserved.
- The question must be plausible according to the context and the assistant description.
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


class DistractingQuestionsGenerator:
    def __init__(self, base_generator: SimpleQuestionGenerator):
        self.base_generator = base_generator

        self.prompt = QAGenerationPrompt(
            system_prompt=DISTRACTING_SYSTEM_PROMPT,
            example_input=DISTRACTING_EXAMPLE_INPUT,
            example_output=DISTRACTING_EXAMPLE_OUTPUT,
            user_input_template=DISTRACTING_INPUT_TEMPLATE,
        )

    def _generate_question(self, context_documents: Sequence[Document]) -> dict:
        generated_qa, question_metadata = self.base_generator._generate_question(context_documents)

        distracting_context = self.base_generator._rng.choice(self.base_generator._vector_store.documents).content
        messages = self.prompt.to_messages(
            assistant_description=self.base_generator._assistant_description,
            language=self.base_generator._language,
            user_input={
                "question": generated_qa["question"],
                "answer": generated_qa["answer"],
                "context": distracting_context,
            },
        )
        question_metadata["difficulty"] = DifficultyLevel.DISTRACTING_ELEMENT
        question_metadata["distracting_context"] = distracting_context
        out = self.base_generator._llm_complete(messages=messages)
        generated_qa["question"] = out["question"]
        return generated_qa, question_metadata
