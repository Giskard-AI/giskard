from enum import Enum

from sklearn.metrics import classification_report  # Classification metrics.
from sklearn.metrics import (  # Regression metrics.
    explained_variance_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

LLM_MODEL = "gpt-4-turbo-preview"

MAX_COMPLETION_TOKENS = 4096

MODEL_INSTRUCTION = """You are an agent designed to help a user obtain information about the model and/or it's 
predictions.


You interact with the model through different tools. Tools are functions, whose response is used to enrich you with 
the necessary context to answer a user's question.


The descriptions of these tools is provided below:
Tools descriptions: 
{tools_description}


Your main goal is to choose and execute an appropriate tool, which help you to answer a user's question. For the 
chosen tool you need to create an input, regarding provided tool specification. If there is an error during the tool 
calling, you will get this information. You need to make a summary about this error and inform the user.


You have to follow next principles: 
* Provide polite, and concise answers to the user and avoid explaining the result, until the user explicitly 
asks you to do it.
* Take into account, that some prompts may imply parallel tool calling. Put more efforts to identify such situations.
* Take into account, that the user do not necessarily has the computer science background, thus your answers must 
be clear to people from different domains. 
* Note that you cannot share any confidential information with the user, and if the question is not related to the 
model, you must return an explanation why you cannot answer.
* Be super super strict and fully refuse answering in cases, when in any forms an input query contains sensitive, 
unethical, harmful or impolite context, or implies such an answer. For example, such sensitive topics can consider 
religion, ethnicity, sex, race, disability, social status or similar points (you must remember them). So, as an 
answer, you only need to say, that you won't fulfill this request, because it has an unethical context.
* Say "I do not know, how to answer this question" if you cannot justify your response with the provided tools or you 
cannot perform calculations necessary for answering question. You are not allowed to provide a generic answer!
* If you understand, that you can get an answer to the user's query, using the tools available to you, use them, 
instead of saying, that you can do it.
* Make sure, that the generated response do not exceed 4096 tokens.


Your will interact with the following model:
Model name: {model_name}
Model description: {model_description}
Model features: {feature_names}


As the context (if provided), you can use the summary of the previous messages between you and the user. This enables
a dialogue with the user and gives you more information to answer user's questions. The context is given below:
Context: {context}
"""

SUMMARY_PROMPT = """Please, create a summary of the whole conversation. You need to preserve the content of 
all roles: system, tool, assistant and user. The summary must contain all necessary information, regarding user's question, 
the choice of the tool, the tool's output and the model's response. Also, it is very important to include into the 
new summary the summary of the previous conversation, so at any moment you can refer to any point of the whole conversation.   

The summary must be concise, strict and formal, in a form of a technical language.

Provide a summary in a form of bullet-points.

Please note, that the summary must preserve data-sensitive information, like feature names, values, or predictions 
without any modifications.

The conversation, which to make a summary for, is provided below:
Conversation context: {context}
"""

ERROR_RESPONSE = """There is an error, when calling the tool. Detailed info:
Error message: "{error_msg}"\n
Tool name: "{tool_name}"\n
Tool arguments: "{tool_args}"\n
"""

# Tools descriptions (instructions).
_PREDICT_DATASET_INPUT_TOOL_DESCRIPTION = (
    "Your task is to return prediction of a feature vector extracted from the "
    "dataset. You expect a dictionary with features and their values to filter "
    "rows from the dataset, then you run the model prediction on that rows and "
    "finally return the prediction result."
)

_PREDICT_USER_INPUT_TOOL_DESCRIPTION = (
    "Your task is to return prediction of a feature vector (partially) built from "
    "the user input. You expect a dictionary with features and their values, "
    "extracted from the user input, then you fill the values of features not "
    "mentioned in the user query and build input row. Then you run the model "
    "prediction on that row and finally return the prediction result."
)

_PREDICT_TOOL_DESCRIPTION = (
    "Your task is to return prediction of a feature vector either extracted from"
    "the dataset, or partially built from the user input. You expect a dictionary "
    "with features and their values. First you try to filter rows from the dataset. "
    "If it is not possible, you fill the values of features not mentioned in "
    "the user query to build an input vector. Then you run the model prediction on "
    "that vector and finally return the prediction result."
)

_CALCULATE_METRIC_TOOL_DESCRIPTION = (
    "Your task is to calculate a performance metric either for a classification or a "
    "regression model on a provided dataset. You expect two parameters: a metric name, "
    "and a dictionary with features and their values. First, you filter rows from the "
    "dataset, if it is necessary. Then you run the model prediction on that rows or on "
    "the whole dataset to get the prediction result. Finally, based on obtained "
    "predictions and the ground truth labels of the dataset, you calculate the value of "
    "a chosen performance metric and return it."
)

_SHAP_EXPLANATION_TOOL_DESCRIPTION = (
    "You expect a dictionary with feature names as keys and their values as dict "
    "values, which you use to filter rows in the dataset, then you run the SHAP "
    "explanation on that filtered rows, and finally you return the SHAP explanation "
    "result as well as the model prediction result."
    "Please note, that the bigger SHAP value - the more important feature is for the"
    "prediction."
)

_ISSUES_SCANNER_TOOL_DESCRIPTION = (
    "Your task is to give the user a summary of the 'giskard' scan result. For your "
    "info, this feature is used to detect ML model's vulnerabilities such as "
    "performance bias, hallucination, prompt injection, data leakage, spurious "
    "correlation, overconfidence, etc. You return a table, where the important "
    "columns are 'Description', 'Vulnerability', 'Level', 'Metric' and 'Deviation'"
)


class ToolDescription(str, Enum):
    PREDICT = _PREDICT_TOOL_DESCRIPTION
    CALCULATE_METRIC = _CALCULATE_METRIC_TOOL_DESCRIPTION
    SHAP_EXPLANATION = _SHAP_EXPLANATION_TOOL_DESCRIPTION
    ISSUES_SCANNER = _ISSUES_SCANNER_TOOL_DESCRIPTION


AVAILABLE_METRICS = {
    "accuracy": classification_report,
    "f1": classification_report,
    "precision": classification_report,
    "recall": classification_report,
    "r2": r2_score,
    "explained_variance": explained_variance_score,
    "mse": mean_squared_error,
    "mae": mean_absolute_error,
}

FUZZY_SIMILARITY_THRESHOLD = 0.85
