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

**Format Instructions**: 
- Score: A score from 1 to 5:
  - 1 meaning that the answer does not respect the criteria at all
  - 3 meaning that the answer can be improved
  - 5 meaning that the answer totally respect the criteria
- Reason: A clear reason on why the score was given
- Tip: A clear and descriptive tip on how to improve the model

{format_instructions}

Example: 
{{"score": 1, "reason": "The answer is missing the required key 'tips' in the json answer", "tip": "You should give example of expected json response to ensure that the schema is respecred"}}
     """
