QA_GENERATION_SYSTEM_PROMPT_WITH_DESCRIPTION = """You are a powerful auditor, your role is to generate question & answer pair from a given list of context paragraphs.

The model you are auditing is the following:
- Model name: {model_name}
- Model description: {model_description}

Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found inside the provided context
- The question must be self-contained
- The question and answer must be in this language: {language}

The user will provide the context, consisting in multiple paragraphs delimited by dashes "------".
You will return the question and the precise answer to the question based exclusively on the provided context.
You must output a single JSON object with keys 'question' and 'answer'. Make sure you return a valid JSON object."""

QA_GENERATION_SYSTEM_PROMPT = """You are a powerful auditor, your role is to generate a question & answer pair from a given list of context paragraphs.

Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found inside the provided context
- The question must be self-contained
- The question and answer must be in this language: {language}

You will be provided the context, consisting in multiple paragraphs delimited by dashes "------".
You will return the question and the precise answer to the question based exclusively on the provided context.
Your output should be a single JSON object, with keys 'question' and 'answer'. Make sure you return a valid JSON object."""

QA_GENERATION_ASSISTANT_EXAMPLE = """{
    "question": "For which countries can I track my shipping?",
    "answer": "We ship to all 50 states in the US, as well as to Canada and Mexico. We offer tracking for all our shippings."
}"""

QA_GENERATION_CONTEXT_EXAMPLE = """What payment methods do you accept?

We accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
"""

FIX_JSON_FORMAT_PROMPT = """Fix the following json string so it contains a single valid json. Make sure to start and end with curly brackets."""


class QAGenerationPrompt:
    system_prompt_with_description = QA_GENERATION_SYSTEM_PROMPT_WITH_DESCRIPTION
    system_prompt_raw = QA_GENERATION_SYSTEM_PROMPT
    example_prompt = QA_GENERATION_CONTEXT_EXAMPLE
    example_answer = QA_GENERATION_ASSISTANT_EXAMPLE

    @classmethod
    def _format_system_prompt(cls, model_name, model_description, language):
        language = language or "en"
        if model_name is not None or model_description is not None:
            system_prompt = cls.system_prompt_with_description.format(
                model_name=model_name,
                model_description=model_description,
                language=language,
            )
        else:
            system_prompt = cls.system_prompt_raw.format(
                language=language,
            )
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        return system_message

    @classmethod
    def _format_example_prompt(cls, examples):
        if examples is not None:
            return examples
        elif cls.example_prompt is not None:
            examples = []
            if cls.example_prompt is not None:
                examples.append({"role": "user", "content": cls.example_prompt})
            if cls.example_prompt is not None:
                examples.append({"role": "assistant", "content": cls.example_answer})
            return examples
        return []

    @classmethod
    def format_context(cls, contexts):
        return "\n------\n".join(["", *[doc.content for doc in contexts], ""])

    @classmethod
    def create_messages(
        cls,
        model_name=None,
        model_description=None,
        language=None,
        add_examples=False,
        examples=None,
        user_content=None,
    ):
        messages = [cls._format_system_prompt(model_name, model_description, language)]
        if add_examples:
            messages.extend(cls._format_example_prompt(examples))

        if user_content is not None:
            messages.append({"role": "user", "content": user_content})

        return messages


COMPLEXIFICATION_SYSTEM_PROMPT_WITH_DESCRIPTION = """You are an expert at writing questions. 
Your task is to re-write questions that will be used to evaluate the following model:
- Model name: {model_name}
- Model description: {model_description}  

Respect the following rules to reformulate the question:
- The re-written question should not be longer than the original question by up to 10 to 15 words. 
- The re-written question should be more elaborated than the original, use elements from the context to enrich the questions. 
- The re-written question should be more difficult to handle for AI models but it must be understood and answerable by humans.
- Add one or more constraints / conditions to the question.
- The re-written question must be in this language: {language}

You will be provided the question delimited by <question></question> tags.
You will also be provided a relevant context which contain the answer to the question, delimited by <context></context> tags. It consists in multiple paragraphs delimited by dashes "------".
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

COMPLEXIFICATION_SYSTEM_PROMPT = """You are an expert at writing questions. 
Your task is to re-write questions that will be used to evaluate a language model.

Respect the following rules to reformulate the question:
- The re-written question should not be longer than the original question by up to 10 to 15 words. 
- The re-written question should be more elaborated than the original, use elements from the context to enrich the questions. 
- The re-written question should be more difficult to handle for AI models but it must be understood and answerable by humans.
- Add one or more constraints / conditions to the question.
- The re-written question must be in this language: {language}

You will be provided the question delimited with <question></question> tags.
You will also be provided a relevant context which contain the answer to the question, delimited with <context></context> tags. It consists in multiple paragraphs delimited by dashes "------".
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

COMPLEXIFICATION_PROMPT_EXAMPLE = """<question>
For which countries can I track my shipping?
</question>

<context>
What payment methods do you accept?

\tWe accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
<context>
"""

COMPLEXIFICATION_ANSWER_EXAMPLE = """{
    "question": "Can you provide my a list of the countries from which I can follow the advancement of the delivery of my shipping?"
}"""


class QuestionComplexificationPrompt(QAGenerationPrompt):
    system_prompt_with_description = COMPLEXIFICATION_SYSTEM_PROMPT_WITH_DESCRIPTION
    system_prompt_raw = COMPLEXIFICATION_SYSTEM_PROMPT
    example_prompt = COMPLEXIFICATION_PROMPT_EXAMPLE
    example_answer = COMPLEXIFICATION_ANSWER_EXAMPLE

    @classmethod
    def format_user_content(cls, question, context):
        context_string = f"<question>\n{question}\n</question>\n<context>\n{context}\n</context>"
        return context_string

    @classmethod
    def create_messages(cls, **kwargs):
        kwargs["user_content"] = cls.format_user_content(*kwargs["user_content"])
        return super().create_messages(**kwargs)


DISTRACTING_QUESTION_SYSTEM_PROMPT = """You are an expert at rewriting question.
Your task is to re-write questions that will be used to evaluate a language model.

Your task is to complexify questions given a provided context. 
Please respect the following rules to generate the question:
- The new question must include a condition or constraint based on the provided context. 
- The new question must have the same answer as the original question.
- The question must be plausible according to the context and the model description.
- The question must be self-contained and understandable by humans. 
- The question must be in this language: {language}

You will be provided the question and its answer delimited with <question></question> and <answer></answer> tags.
You will also be provided a context paragraph delimited with <context></context> tags.
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

DISTRACTING_QUESTION_SYSTEM_PROMPT_WITH_DESCRIPTION = """You are an expert at rewriting questions.
Your task is to re-write questions that will be used to evaluate the following model:
- Model name: {model_name}
- Model description: {model_description}  

Your task is to complexify questions given a provided context. 
Please respect the following rules to generate the question:
- The new question must include a condition or constraint based on the provided context. 
- The original question direction should be preserved.
- The question must be plausible according to the context and the model description.
- The question must be self-contained and understandable by humans. 
- The question must be in this language: {language}

You will be provided the question delimited with <question></question> tags.
You will also be provided a context paragraph delimited with <context></context> tags.
You will return the reformulated question as a single JSON object, with the key 'question'. Make sure you return a valid JSON object.
"""

DISTRACTING_QUESTION_USER_INPUT = """<question>
{question}
</question>
<answer>
{answer}
</answer>
<context>
{context}
</context>"""

DISCTRACTING_QUESTION_PROMPT_EXAMPLE = DISTRACTING_QUESTION_USER_INPUT.format(
    question="What job offer do you have for engineering student?",
    answer="We have plenty of different jobs for engineering student depending on your speciality: mechanical engineer, data scientist, electronic designer and many more.",
    context="Sometimes employers assume being accessible and inclusive only means providing physical access like ramps, accessible bathrooms and automatic opening doors. However, there are many other important ways to demonstrate that you welcome and want to attract a diverse workforce including people with disability.",
)

DISCTRACTING_QUESTION_ANSWER_EXAMPLE = """{
    "question": "Do you have any job opening suitable for engineering students with a disability? "
}"""


class DistractingQuestionPrompt(QuestionComplexificationPrompt):
    system_prompt_with_description = DISTRACTING_QUESTION_SYSTEM_PROMPT_WITH_DESCRIPTION
    system_prompt_raw = DISTRACTING_QUESTION_SYSTEM_PROMPT
    example_prompt = DISCTRACTING_QUESTION_PROMPT_EXAMPLE
    example_answer = DISCTRACTING_QUESTION_ANSWER_EXAMPLE

    @classmethod
    def format_user_content(cls, question, answer, context):
        return DISTRACTING_QUESTION_USER_INPUT.format(question=question, answer=answer, context=context)
