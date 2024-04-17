from itertools import cycle

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from giskard.llm.client.copilot import ToolChatMessage

type_error_patterns = {
    "question_dataset": r"(?:BaseModel\.)?talk\(\) missing 2 required positional arguments: 'question' and 'dataset'",
    "dataset": r"(?:BaseModel\.)?talk\(\) missing 1 required positional argument: 'dataset'",
    "question": r"(?:BaseModel\.)?talk\(\) missing 1 required positional argument: 'question'",
}

default_question = "What can you do?"
test_default_llm_responses = cycle(
    [
        ToolChatMessage(
            role="assistant",
            content="I can assist you with various tasks related to a Titanic binary classification model, "
            "which predicts whether a passenger survived or not in the Titanic incident. Here's what I can "
            "do:\n\n1. **Predict Survival**: I can predict whether a passenger survived or not based on their "
            "details such as class, sex, age, number of siblings/spouses aboard, number of parents/children "
            "aboard, fare, and port of embarkation.\n\n2. **Estimate Model Performance Metrics**: I can "
            "calculate performance metrics like accuracy, F1 score, precision, recall, R2 score, RMSE, MSE, "
            "and MAE for the model based on the provided dataset or a subset of it.\n\n3. **Provide SHAP "
            "Explanations**: I can offer explanations for the model's predictions using SHAP values, "
            "which help understand the impact of each feature on the prediction.\n\n4. **Scan for Model "
            "Performance Issues**: I can give you a summary of the model's vulnerabilities, "
            "such as unrobustness, underconfidence, unethical behavior, data leakage, performance bias, "
            "and more.\n\nFeel free to ask for any of these services or if you have any questions related to "
            "the Titanic binary classification model!",
        ),
        ToolChatMessage(
            role="assistant",
            content="- The user inquires about the capabilities of the assistant.\n- The assistant responds by "
            "detailing its capabilities related to a Titanic binary classification model, which include:\n  "
            "1. Predicting survival based on passenger details.\n  2. Estimating model performance metrics.\n "
            " 3. Providing SHAP explanations for model predictions.\n  4. Scanning for model performance "
            "issues.",
        ),
    ]
)

predict_tool_question = "Give me predictions of the model on a given dataset. Use 'predict' tool."
test_predict_tool_llm_responses = cycle(
    [
        ToolChatMessage(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCall(
                    id="call_GeMR17xALaOSuh1NqnBJIuVP",
                    type="function",
                    function=Function(name="predict", arguments='{"features_dict": {}}'),
                )
            ],
        ),
        ToolChatMessage(
            role="assistant",
            content='The model has provided predictions for the given dataset. The predictions include both "yes" ('
            'survived) and "no" (did not survive) outcomes for various passengers. If you need more detailed '
            "information or have specific questions about these predictions, feel free to ask!",
        ),
        ToolChatMessage(
            role="assistant",
            content="- User requested predictions from the Titanic binary classification model on a given dataset "
            "using the 'predict' tool.\n- The 'predict' tool returned a series of predictions indicating "
            'whether passengers survived ("yes") or did not survive ("no").\n- The assistant summarized the '
            "tool's output, informing the user that the model provided predictions for the dataset, "
            'including both "yes" (survived) and "no" (did not survive) outcomes for various passengers, '
            "and offered further assistance if needed.",
        ),
    ]
)

shap_tool_question = "Calculate SHAP values of each feature. Use 'shap_explanation' tool."
test_shap_tool_llm_responses = cycle(
    [
        ToolChatMessage(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCall(
                    id="call_B55HjJ2TNHvNo1cohsaOV4nS",
                    type="function",
                    function=Function(name="shap_explanation", arguments='{"features_dict": {}}'),
                )
            ],
        ),
        ToolChatMessage(
            role="assistant",
            content="The SHAP values for each feature have been calculated successfully. Here's a summary of the "
            "results:\n\n- **PassengerId**: The SHAP values vary across different passengers, indicating "
            "varying degrees of importance for this feature in the model's predictions.\n- **Pclass**: Higher "
            "classes (e.g., 1st class) generally have higher SHAP values, suggesting a strong influence on "
            "survival prediction.\n- **Name**: The SHAP values for names vary, indicating that specific names "
            "or titles may have some influence on the model's predictions.\n- **Sex**: Being female has a "
            "significantly higher SHAP value, indicating a strong positive influence on the prediction of "
            "survival.\n- **Age**: Younger ages tend to have higher SHAP values, suggesting that age "
            "influences survival predictions, with younger passengers having a higher likelihood of "
            "survival.\n- **SibSp**: The number of siblings/spouses aboard has varying SHAP values, "
            "indicating it influences predictions to different extents for different passengers.\n- "
            "**Parch**: The number of parents/children aboard has varying SHAP values, similar to SibSp, "
            "indicating its influence on survival predictions.\n- **Fare**: Higher fares generally have "
            "higher SHAP values, suggesting that passengers who paid more had a higher likelihood of "
            "survival.\n- **Embarked**: The port of embarkation has varying SHAP values, with some ports "
            "showing a stronger influence on survival predictions than others.\n\nThese results indicate that "
            "features like sex, passenger class, and fare play significant roles in the model's predictions, "
            "while other features like name, age, and family aboard also contribute to varying extents.",
        ),
        ToolChatMessage(
            role="assistant",
            content="- The user requested the calculation of SHAP values for each feature using the "
            "'shap_explanation' tool.\n- The tool provided SHAP values for features: 'PassengerId', 'Pclass', "
            "'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked', along with the prediction results "
            "for a set of passengers.\n- The assistant summarized the SHAP values, highlighting the influence "
            "of features like 'Sex', 'Pclass', 'Fare', 'Age', 'SibSp', 'Parch', and 'Embarked' on the model's "
            "survival predictions. It noted significant roles for sex, passenger class, and fare, with other "
            "features contributing to varying extents.",
        ),
    ]
)

metric_tool_question = (
    "If the model is classification, calculate accuracy. If regression, then calculate R2 score. Use "
    "'calculate_metric' tool."
)
test_metric_tool_llm_responses = cycle(
    [
        ToolChatMessage(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCall(
                    id="call_rdqJGVFzrW4gfpuEEtihBBsG",
                    type="function",
                    function=Function(
                        name="calculate_metric", arguments='{"features_dict": {}, "metric_type": "accuracy"}'
                    ),
                )
            ],
        ),
        ToolChatMessage(role="assistant", content="The accuracy of the model is 0.79.", tool_calls=None),
        ToolChatMessage(
            role="assistant",
            content="- The user requested the calculation of accuracy for a classification model or R2 score for a "
            "regression model using the 'calculate_metric' tool.\n- The tool was called with the appropriate "
            "parameters to calculate the metric.\n- The tool's output indicated a test failure but provided a "
            "metric value of 0.79.\n- The assistant informed the user that the accuracy of the model is 0.79, "
            "interpreting the metric value provided by the tool.",
        ),
    ]
)

scan_tool_question = "Tell me, which performance issues/vulnerabilities does the model have. Use 'issues_scanner' tool."
test_scan_tool_llm_responses_1 = cycle(
    [
        ToolChatMessage(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCall(
                    id="call_u7gekjksLI08eRcGU7Bb0HEY",
                    type="function",
                    function=Function(name="issues_scanner", arguments="{}"),
                )
            ],
        ),
        ToolChatMessage(
            role="assistant",
            content="The model has been identified to have the following performance issues and "
            "vulnerabilities:\n\n1. **Robustness issues**: The model's predictions change in 6.67% of the "
            'cases when the feature "Name" is transformed to title case, which was not expected.\n\n2. '
            "**Overconfidence issues**: The model shows a significantly higher number of overconfident wrong "
            'predictions in several data slices, including when:\n   - The `Name` contains "mr".\n   - The '
            "`text_length(Name)` is less than 28.500.\n   - The `Fare` is less than 14.850.\n   - The `Sex` "
            'is "male".\n   - The `Parch` is 0.\n   - The `SibSp` is 0.\n\n3. **Spurious Correlation '
            "issues**: The model exhibits spurious correlations, such as:\n   - A high association between "
            '`Sex` == "female" and the prediction of Survived = `yes`.\n   - A high association between `Sex` '
            '== "male" and the prediction of Survived = `no`.\n   - A high association between `Name` '
            'containing "mr" and the prediction of Survived = `no`.\n\n4. **Performance issues**: The model '
            'has performance issues in various data slices, including lower Recall for `Name` containing "mr" '
            'and `Sex` == "male", lower Precision for `Pclass` == 3, and lower Accuracy for `Name` containing '
            '"master" and `Embarked` == "S", among others.\n\nThese issues highlight the model\'s '
            "vulnerabilities in handling certain transformations, overconfidence in predictions, "
            "spurious correlations, and performance discrepancies across different data slices.",
        ),
        ToolChatMessage(
            role="assistant",
            content="- The user requested information on the performance issues/vulnerabilities of the model using "
            "the 'issues_scanner' tool.\n- The 'issues_scanner' tool identified several vulnerabilities, "
            "including robustness issues, overconfidence issues, spurious correlation issues, and performance "
            'issues across various data slices.\n  - Robustness issues were noted when the "Name" feature was '
            "transformed to title case, affecting predictions in 6.67% of cases.\n  - Overconfidence issues "
            'were observed in data slices where the "Name" contains "mr," the text length of "Name" is less '
            'than 28.500, the "Fare" is less than 14.850, the "Sex" is "male," the "Parch" is 0, '
            'and the "SibSp" is 0.\n  - Spurious correlation issues were found with a high association '
            'between "Sex" being "female" and predicting Survived = "yes," "Sex" being "male" and predicting '
            'Survived = "no," and "Name" containing "mr" and predicting Survived = "no."\n  - Performance '
            'issues were identified in data slices with lower Recall for "Name" containing "mr" and "Sex" == '
            '"male," lower Precision for "Pclass" == 3, and lower Accuracy for "Name" containing "master" and '
            '"Embarked" == "S," among others.\n- The assistant summarized these findings, highlighting the '
            "model's vulnerabilities in handling certain transformations, its overconfidence in predictions, "
            "the presence of spurious correlations, and performance discrepancies across different data "
            "slices.",
        ),
    ]
)

test_scan_tool_llm_responses_2 = cycle(
    [
        ToolChatMessage(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCall(
                    id="call_88KzczVdOyoakLNBLp6SosCp",
                    type="function",
                    function=Function(name="issues_scanner", arguments="{}"),
                )
            ],
        ),
        ToolChatMessage(
            role="assistant",
            content="There was an error when trying to obtain information about the model's performance issues or "
            'vulnerabilities. The error message is: "To obtain information about issues detected by the '
            "Giskard Scan, provide the 'scan_report' argument.\" It seems I need to provide additional "
            "information to proceed with your request.",
        ),
        ToolChatMessage(
            role="assistant",
            content="- The user requested information on the performance issues or vulnerabilities of a model using "
            "the 'issues_scanner' tool.\n- The 'issues_scanner' tool call resulted in an error due to missing "
            "the 'scan_report' argument.\n- The assistant informed the user about the error and the need for "
            "additional information to proceed with the request.",
        ),
    ]
)
