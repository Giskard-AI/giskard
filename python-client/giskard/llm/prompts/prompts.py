VALIDATE_TEST_CASE = """
You are a prompt QA tasked with evaluate LLM answer based on test assertions of the {model_name} model.

**Scope**: Please focus on testing '{test_case}'.

**Description**: The objective is to validate that the model answer related to the user prompt correctly pass the test.

**Model Information**:
``` 
{model_description}
```

**User Inputs**:

```json
{prompt}
```

**Model Answer**:
{response}

**Format Instructions**: True meaning that the test passed, false meaning that the test failed:

{format_instructions}

Example: 
{{"result": false, "reason": "The answer is missing the required key 'tips' in the json answer", "tip": "You should give example of expected json response to ensure that the schema is respecred"}}
     """
