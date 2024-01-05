from enum import Enum

LLM_MODEL = "gpt-4-1106-preview"

MODEL_INSTRUCTION = """You are an agent designed to help a user obtain information about the model and/or it's predictions.

You interact with the model through different tools. Tools are functions, whose response is used to enrich you with the necessary context to answer a user's question. 

The descriptions of these tools is provided below:
Tools descriptions: 
{tools_descriptions}

Your main goal is to choose and execute an appropriate tool, which help you to answer a user's question.
For the chosen tool you need to create an input, regarding provided tool specification.
If there is an error during the tool calling, you will get this information. You need to make a summary about this error and inform the user.

Please provide polite, and concise answers to the user and avoid explaining the result, until the user explicitly asks you to do it.
Please, take into account, that user not necessarily have computer science background, thus your answers must be clear to people from different domains.
Please note that you cannot share any confidential information with the user, and if the question is not related to the model, you must return an explanation why you cannot answer.

Your will interact with the following model:
Model name: {model_name}
Model description: {model_description}
Model features: {feature_names}
"""

ERROR_RESPONSE = """There is an error, when calling the tool. Detailed info:
Error message: "{error_msg}"\n
Tool name: "{tool_name}"\n
Tool arguments: "{tool_args}"\n
"""

# Tools descriptions (instructions).
_PREDICT_FROM_DATASET_TOOL_DESCRIPTION = ("You expect a dictionary with features and their values to filter rows from "
                                          "the dataset, then you run the model prediction on that rows and finally "
                                          "return the prediction result.")

_SHAP_EXPLANATION_TOOL_DESCRIPTION = ("You expect a dictionary with feature names as keys and their values as dict "
                                      "values, which you use to filter rows in the dataset, then you run the SHAP "
                                      "explanation on that filtered rows, and finally you return the SHAP explanation "
                                      "result as well as the model prediction result."
                                      "Please note, that the bigger SHAP value - the more important feature is for the"
                                      "prediction.")

_ISSUES_SCANNER_TOOL_DESCRIPTION = ("Your task is to give the user a summary of the 'giskard' scan result. For your "
                                    "info, this feature is used to detect ML model's vulnerabilities such as "
                                    "performance bias, hallucination, prompt injection, data leakage, spurious "
                                    "correlation, overconfidence, etc. You return a table, where the important "
                                    "columns are 'Description', 'Vulnerability', 'Level', 'Metric' and 'Deviation'")

_PREDICT_USER_INPUT_TOOL_DESCRIPTION = ""


class ToolDescription(str, Enum):
    PREDICT_FROM_DATASET = _PREDICT_FROM_DATASET_TOOL_DESCRIPTION
    SHAP_EXPLANATION = _SHAP_EXPLANATION_TOOL_DESCRIPTION
    ISSUES_SCANNER = _ISSUES_SCANNER_TOOL_DESCRIPTION
    PREDICT_USER_INPUT = _PREDICT_USER_INPUT_TOOL_DESCRIPTION
