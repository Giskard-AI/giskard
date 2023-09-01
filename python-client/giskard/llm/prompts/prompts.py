VALIDATE_TEST_CASE = """
You are a teacher.
Your task is to verify that the response of the following prompt pass this test case: {test_case}

Note that if you have doubt or if the response seems unrelated to the test case, it means the test case fails

Model:
```
{prompt}
```

Response:
```
{response}
```

Please remember to evaluate the response of the prompt based on the given test case

Make sure to provide the response for the following JSON template;
true meaning that the test passed, false meaning that the test failed:

{format_instructions}

Example: 
{{"result": true}}
    """
