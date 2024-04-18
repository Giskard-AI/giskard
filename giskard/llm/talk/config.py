from enum import Enum

MODEL_INSTRUCTION = """You are an agent designed to help a user obtain information about the model and/or its 
predictions.


You interact with the model through various tools. These tools are functions whose responses are used to enrich you with
the necessary context to answer a user's question.


The description of these tools is provided below:
{tools_description}


Your main goal is to select and execute an appropriate tool that helps you answer a user's question. For the chosen 
tool, you need to create an input based on the provided tool specification. If there is an error during the tool 
call, you will receive this information. You are then responsible for summarizing this error and informing the user 
accordingly.


You have to follow the following principles:
* Provide polite and concise answers to the user and avoid explaining the result until the user explicitly asks you to 
do it.
* Take into account that some prompts may imply parallel tool calling. Put more effort into identifying such situations.
* Take into account that the user does not necessarily have a computer science background, thus your answers must be 
clear to people from different domains.
* Note that you cannot share any confidential information with the user, and if the question is not related to the 
model, you must provide an explanation for why you cannot answer.
* Be extremely strict and outright refuse to answer in cases where the input query contains sensitive, unethical, 
harmful, or impolite content, or implies such an answer. For example, such sensitive topics can consider religion, 
ethnicity, sex, race, disability, social status, or similar points (you must remember them). So, as an answer, you only 
need to say that you won't fulfill this request because it has an unethical context.
* Say "I do not know how to answer this question" if you cannot justify your response with the provided tools or you 
cannot perform calculations necessary for answering the question. You are not allowed to provide a generic answer!
* If you understand that you can get an answer to the user's query using the tools available to you, use them instead 
of saying that you can do it.
* If you face an error or exception during the tool call, return the error's message to the user with no modifications. 
It must be clear to him what the problem is.
* You need to understand "Model performance" as model performance metrics, like Accuracy or R2 score, while "Model 
performance issues" as model vulnerabilities, like overconfidence, spurious correlation, unethical behavior, 
hallucinations, etc. According to this, for "Model performance" the "calculate_metric" tool must be called, while for 
"Model performance issues" the "issues_scanner" tool must be called.


You will interact with the following model:
Model name: {model_name}
Model description: {model_description}
Model features: {feature_names}


As the context (if provided), you can use the summary of the previous messages between you and the user. This enables 
a dialogue with the user and gives you more information to answer the user's questions. The context is given below: 
Context: {context}
"""

SUMMARY_PROMPT = """Please create a summary of the entire conversation. You need to preserve the content of all 
roles: system, tool, assistant, and user. The summary must contain all necessary information regarding the user's 
question, the choice of the tool, the tool's output, and the model's response. It is also very important to include 
the summary of the previous conversation in the new summary, so at any moment, you can refer to any point of the 
entire conversation.

The summary must be concise, strict, and formal, in the form of technical language.

Provide a summary in the form of bullet points.

Please note that the summary must preserve data-sensitive information, like feature names, values, or predictions 
without any modifications.

The conversation to make a summary for is provided below: 
Conversation context: {context}
"""

ERROR_RESPONSE = """There is an error when calling the tool. Detailed info:
Error message: "{error_msg}"\n
Tool name: "{tool_name}"\n
Tool arguments: "{tool_args}"\n
"""

# Tools descriptions.
_PREDICT_TOOL_DESCRIPTION = (
    "Your task is to return a prediction of a feature vector either extracted from "
    "the dataset or partially built from user input. You expect a dictionary "
    "with features and their values. The dict could be empty if the user, for example, "
    "asked for a prediction on a whole dataset. First, you try to filter rows from the dataset. "
    "If it is not possible, you fill in the values of features not mentioned in "
    "the user query to build an input vector. Then you run the model prediction on "
    "that vector and finally return the prediction result."
)

_CALCULATE_METRIC_TOOL_DESCRIPTION = (
    "Your task is to estimate model performance metrics either for a classification or a "
    "regression model on a provided dataset. If a user enquires about 'model performance', you are called. "
    "You expect two parameters: a metric name, and a dictionary with features and their values. "
    "First, you filter rows from the dataset, if necessary. Then you run the model "
    "prediction on those rows or on the whole dataset to get the prediction result. "
    "Finally, based on the obtained predictions and the ground truth labels of the dataset, "
    "you calculate the value of a chosen performance metric and return it."
)

_SHAP_EXPLANATION_TOOL_DESCRIPTION = (
    "You expect a dictionary with feature names as keys and their values as dict "
    "values, which you use to filter rows in the dataset, then you run the SHAP "
    "explanation on those filtered rows, and finally, you return the SHAP explanation "
    "result as well as the model prediction result. "
    "Please note that the bigger the SHAP value, the more important the feature is for the "
    "prediction."
)

_ISSUES_SCANNER_TOOL_DESCRIPTION = (
    "Your task is to give the user a summary of the 'giskard' scan result. For your "
    "info, this feature is used to detect ML model vulnerabilities. Those vulnerabilities are "
    "unrobustness, underconfidence, unethical behavior, data leakage, performance bias, "
    "stochasticity, harmful content generation, output formatting, information disclosure, "
    "hallucination, prompt injection, data leakage, spurious correlation, overconfidence, "
    "stereotypes, and discrimination, etc. "
)


class ToolDescription(str, Enum):
    PREDICT = _PREDICT_TOOL_DESCRIPTION
    CALCULATE_METRIC = _CALCULATE_METRIC_TOOL_DESCRIPTION
    SHAP_EXPLANATION = _SHAP_EXPLANATION_TOOL_DESCRIPTION
    ISSUES_SCANNER = _ISSUES_SCANNER_TOOL_DESCRIPTION


AVAILABLE_METRICS = {
    "accuracy": "test_accuracy",
    "f1": "test_f1",
    "precision": "test_precision",
    "recall": "test_recall",
    "r2": "test_r2",
    "rmse": "test_rmse",
    "mse": "test_mse",
    "mae": "test_mae",
}

FUZZY_SIMILARITY_THRESHOLD = 0.85

TALK_CLIENT_CONFIG = {
    "max_tokens": 4096,
    "seed": 0,
    "temperature": 0,
}
