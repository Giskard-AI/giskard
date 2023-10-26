import openai
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(3))
def llm(messages, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, n=n, **kwargs)
    if n == 1:
        return completion.choices[0].message.content
    return [c.message.content for c in completion.choices]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(3))
def llm_fn_call(messages, functions, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(
        model=model, messages=messages, functions=functions, temperature=temperature, n=n, **kwargs
    )
    if n == 1:
        return completion.choices[0].message
    return [c.message for c in completion.choices]
