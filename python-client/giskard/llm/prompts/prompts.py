VALIDATE_TEST_CASE = """
I am a prompt QA responsible for evaluating the LLM answer based on test assertions of the {model_name} model. 

**Scope**: Please focus on testing '{test_case}'.

**Description**: The objective is to verify that the model answer related to the user prompt passes the test correctly.

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
Please provide a JSON object as a response, including the following keys:
- Score: A number ranging from 1 to 5:
  - 1 indicates that the answer does not meet the criteria at all
  - 3 indicates that the answer can be improved
  - 5 indicates that the answer completely meets the criteria
- Reason: A text that clearly explains the given score
- Tip: A text that offers a clear and descriptive suggestion on how to enhance the model

Example: 
{{"score": 1, "reason": "The answer is missing the required key 'tips' in the JSON response", "tip": "To ensure that the schema is respected, provide an example of the expected JSON response"}}
"""
