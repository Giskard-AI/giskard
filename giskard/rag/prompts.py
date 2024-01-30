QA_GENERATION_SYSTEM_PROMPT_MODEL = """You are a powerful auditing AI, your role is to generate question answer pair from a given list of context paragraph to audit a model specialized on these knowledge. 

The model you are auditing is the following:
- Model name: {model_name}
- Model description: {model_description}  

Your task is to generate questions about the products, the ordering process and the shop's activities in general. Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found inside the provided context
- The question must be self-contained
- The question and answer must be in this language: {language}

You will be provided the context, consisting in multiple paragraphs delimited by dashes "------".
You will return the question and the precise answer to the question based exclusively on the provided context.
Your output should be a single JSON object, with keys 'question' and 'answer'. Make sure you return a valid JSON object."""

QA_GENERATION_SYSTEM_PROMPT = """You are a powerful auditing AI, your role is to generate question answer pair from a given list of context paragraph to audit a model specialized on these knowledge. 

Your task is to generate questions about the products, the ordering process and the shop's activities in general. Your question must be related to a provided context.  
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

\tWe accept a variety of payment methods to provide our customers with a convenient and secure shopping experience. You can make a purchase using major credit and debit cards, including Visa, Mastercard, American Express, and Discover. We also offer the option to pay with popular digital wallets such as PayPal and Google Pay. For added flexibility, you can choose to complete your order using bank transfers or wire transfers. Rest assured that we prioritize the security of your personal information and go the extra mile to ensure your transactions are processed safely.
------
\tWhat is your shipping policy?

We offer free shipping on all orders over $50. For orders below $50, we charge a flat rate of $5.99. We offer shipping services to customers residing in all 50\n states of the US, in addition to providing delivery options to Canada and Mexico.
------
\tHow can I track my order?

Tracking your order is a breeze! Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. Enter your tracking number, and you will be able to monitor the progress of your shipment in real-time. This way, you can stay updated on the estimated delivery date and ensure you're available to receive your package.
"""

FIX_JSON_FORMAT_PROMPT = """Fix the following json string so it contains a single valid json. Make sure to start and end with curly brackets."""
