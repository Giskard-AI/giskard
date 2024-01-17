QUESTION_GENERATION_PROMPT = """You are a client from an online shop called {model_name}. Shop description: {model_description}
You are looking for information about specific products that are sold on by this shop and about the shop's activities.   

Your task is to generate questions about the products, the ordering process and the shop's activities in general. Your question must be related to a provided context.  
Please respect the following rules to generate the question:
- The answer to the question should be found, at least partially, inside the provided context.  
- The question must be self-contained and understandable by humans. 
- The question must be in {language}.

Here is the context:
<context>
{context}
</context>

Remember you are a client of {model_name}, you are looking for information to help you with your shopping.
Please call the `generate_inputs` function with the generated inputs. You must generate 1 input.
"""

ANSWER_GENERATION_PROMPT = """Your task is to answer a question based on a provided context.
The answer should be clear and concise. Think step by step and answer the question thoroughly. 
Your answer must only contain information provided by the context.

Here is the context and the question:
<context>
{context}
</context>

<question>
{question}
</question>

Please call the `generate_inputs` function with the generated inputs.
"""
