FIND_CATEGORY_PROMPT = """
You are an prompt QA, your goal is to write a list of use case for a prompt to be tested.

Please generate a JSON list of strings representing clear and concrete real-life scenarios where a prompt might be used.

Make sure that the use cases are varied and cover nominal and edge cases. Make sure the scenario are a concise description of the expected behaviour.

```
{prompt_template}
```

{format_instructions}

Example: 
{{"objectives": ["Generate a reply to an email", "Summarise the message for non technical user", "Generate a polite declination message"]}}
"""

FIND_CATEGORY_PROMPT_FAILED_SUFFIX = " "

GENERATE_INPUT_PROMPT = """
You are an prompt QA, your goal is to write an input for the following use case: "{category}"

Please generate a the textual input value for all the variable defined inside brackets: {variables}.

Ensure that the input variables represent clear and concrete values for a real-life scenario related to the given use case.

We will use the input variables to generate the answer and validate the response, so it's important that the input variables are coherent and meaningful.


```
{prompt_template}
```

{format_instructions}

Example: 
{{"input": {{"instruction": "Ask to reschedule on Tuesday at 2PM", "text": "I hereby confirm our interview next Monday at 10AM"}}}}
"""

GENERATE_INPUT_PROMPT_FAILED_SUFFIX = (
    "The goal is to generate realistic and detailed prompt where the model might fail to answer properly"
)

GENERATE_TEST_PROMPT = """
You are an prompt QA, your goal is to write a list of assertion for a model to be tested on its generated answer.

Please generate assertions that the answer must pass. 

Make sure that the assertions are varied and cover nominal and edge cases. Make sure the assertions are a concise description of the expected behaviour. 

Please make sure that the assertion validate the answer for any given input fed inside the brackets of the following model:

```
{prompt_template}
```

{format_instructions}

Example: 
{{"assertions": ["The answer must contains an explanation", "The answer must be a valid JSON string"]}}
"""
