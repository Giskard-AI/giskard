# 🗣🤖💡AI Quality Copilot
> ⚠️ **AI Quality Copilot is currently in early version and is subject to change**. Feel free to reach out on our [Discord server](https://discord.gg/fkv7CAr3FE) if you have any trouble or to provide feedback.

Obtaining information about the ML model requires some coding effort. It may be time-consuming and create friction when 
one seeks prediction results, explanations, or the model's performance. The reality is that the code simply translates 
the user's intent, which can be described in natural language. For instance, the phrase 'What are the predictions for 
women across the dataset?' could be converted to the `model.predict(df[df.sex == 'female'])` snippet. However, in many 
cases, such transformation is not as straightforward and may require some effort compared to forming the query in 
natural language.

To address this issue, we introduce the **AI Quality Copilot** - an LLM agent that facilitates accessing essential 
information about the model's predictions, explanations, performance metrics, and issues through a natural language 
interface. Users can prompt the Copilot, and it will provide the necessary information about the specified ML model. In 
essence, instead of writing code, one can simply "talk" to the model.

## How it works?
"The AI Quality Copilot is an LLM agent that, based on a user's input query, determines which function to call along 
with its arguments. The output of these functions will then be used to provide an answer. To utilize it, all you need to
do is call the talk method of the Giskard model and provide a question about the model."

We implemented this feature using the OpenAI [function calling API](https://platform.openai.com/docs/guides/function-calling). 
This approach expands the standard capabilities of LLM agents by enabling them to utilize a predefined set of python
functions or tools designed for various tasks. The concept is to delegate to the agent the decision on which tool to use
in order to provide a more effective response to the user's question.

AI Quality Copilot is capable of providing the following information about the ML model:
1. `Prediction` on records from the given dataset or the user's input.
2. `Prediction explanation` using the SHAP framework.
3. `Performance metrics` for classification and regression tasks.
4. `Performance issues` detected using the Giskard Scan.

## Before starting
First, ensure that you have installed the `talk` flavor of Giskard:
```bash
pip install "giskard[talk]"
```

To utilize the AI Quality Copilot, you'll need an OpenAI API key. You can set it in your notebook like this:
```python
import os

os.environ["OPENAI_API_KEY"] = "sk-…"
```

## Prepare the necessary artifacts
First, set up the Giskard dataset:
```python
giskard_dataset = giskard.Dataset(df, target=TARGET_COLUMN, name="Titanic dataset", cat_columns=CATEGORICAL_COLUMNS)
```

Next, it is mandatory to set up the Giskard model, which we will interact with. It's important to provide a detailed 
description as well as the name of the model to enhance the responses of the AI Quality Copilot.
```python
giskard_model = giskard.Model(
    model=prediction_function,
    model_type="classification",  # Currently, the Quality Copilot supports either classification or regression.
    classification_labels=CLASSIFICATION_LABELS,
    feature_names=FEATURE_NAMES,
    # Important for the Quality Copilot.
    name="Titanic binary classification model",
    description="The binary classification model, which predicts, whether the passenger survived or not in the Titanic incident. \n"
                "The model outputs yes, if the person survived, and no - if he died."
)
```

Lastly, generate the Giskard scan report. This dependency is optional, and if you don't need information about the 
model's performance issues, you can omit this step.
```python
scan_result = giskard.scan(giskard_model, giskard_dataset)
```

## AI Quality Copilot
Let's finally try the AI Quality Copilot. The primary and only method to interact with it is through the `talk` method 
of the Giskard model. Below is the API for the method:
```python
def talk(self, question: str, dataset: Dataset, scan_report: ScanReport = None, context: str = "") -> TalkResult:
        """Perform the 'talk' to the model.

        Given `question`, allows to ask the model about prediction result, explanation, model performance, issues, etc.

        Parameters
        ----------
        question : str
            User input query.
        dataset : Dataset
            Giskard Dataset to be analysed by the 'talk'.
        context : str
            Context of the previous 'talk' results. Necessary to keep context between sequential 'talk' calls.
        scan_report : ScanReport
            Giskard Scan Report to be analysed by the 'talk'.
        """
```

We'll start with a simple example. We'll ask the AI Quality Copilot what it can do:
```python
giskard_model.talk(question="What can you do?", dataset=giskard_dataset)
```

The agent's response is as follows:
```markdown
I can assist you with various tasks related to a Titanic binary classification model, which predicts whether a passenger survived or not in the Titanic incident. Here's what I can do:

1. **Predict Survival**: I can predict whether a passenger survived or not based on their details such as class, sex, age, number of siblings/spouses aboard, number of parents/children aboard, fare, and port of embarkation.

2. **Model Performance Metrics**: I can estimate model performance metrics such as accuracy, F1 score, precision, recall, R2 score, explained variance, mean squared error (MSE), and mean absolute error (MAE) for the Titanic survival prediction model.

3. **SHAP Explanations**: I can provide SHAP explanations for predictions, which help understand the impact of each feature on the model's prediction.

4. **Model Vulnerabilities Scan**: I can give you a summary of the model's vulnerabilities, such as unrobustness, underconfidence, unethical behavior, data leakage, performance bias, and more.

Please let me know how I can assist you!
```
In this example, the agent informs about the tasks it can perform without actually executing them, as there is no need 
to do so.

### Prediction
Now, let's ask the agent to provide information about the model's prediction on a specific record from the dataset:
```python
giskard_model.talk(question="Have 'Minahan miss Daisy E' survived in the Titanic incident?", dataset=giskard_dataset)
```

Response:
```markdown
Yes, Minahan Miss Daisy E survived in the Titanic incident.
```
This example demonstrates how the AI Quality Copilot allows us to avoid writing code to obtain a prediction on a dataset
record. Instead, we can simply use natural language.

### Prediction explanation
The next example demonstrates how we can obtain the prediction explanation in a similar manner:
```python
giskard_model.talk(question="What was important for the survival result of Minahan, Miss. Daisy E?", dataset=giskard_dataset)
```
```markdown
For Minahan, Miss. Daisy E, the most important factors for the survival prediction (yes) were:
- Sex ('female') with a SHAP value of 0.493
- Pclass (1) with a SHAP value of 0.316
- Embarked ('Q') with a SHAP value of 0.068

These values indicate that being female, traveling in the first class, and embarking from 'Q' were significant contributors to the model's prediction of survival.
```
Once again, no manual coding is needed from us to obtain this result! Everything is managed and executed by the AI 
Quality Copilot.

### Performance metrics
Now let's calculate the model's accuracy:
```python
giskard_model.talk(question="Calculate accuracy of the model.", dataset=giskard_dataset)
```
```markdown
The accuracy of the model is 0.79.
```

### Performance issues
Finally, we can ask an LLM agent about the model's performance issues. It's mandatory to provide the generated scan 
report in this case.
```python
giskard_model.talk(question="Does the model has any performance issues or biases?", dataset=giskard_dataset, scan_report=result)
```

```markdown
The model has been identified to have several performance issues and biases, including:

1. **Robustness issues**: The model's predictions change when the "Name" feature is transformed to title case in 6.67% of the cases, which indicates a medium level of robustness issue.
2. **Overconfidence issues**: The model shows a significantly higher number of overconfident wrong predictions in several data slices, including when the "Name" contains "mr", when the text length of "Name" is less than 28.5, when "Fare" is less than 14.85, when "Sex" is "male", when "Parch" is 0, and when "SibSp" is 0. These issues are mostly major, indicating a high level of overconfidence in wrong predictions.
3. **Spurious Correlation issues**: There are minor issues related to spurious correlations, particularly with the "Sex" feature being highly associated with the survival prediction. For example, "female" is highly associated with "Survived" = "yes", and "male" is highly associated with "Survived" = "no".
4. **Performance issues**: The model has major performance issues in several data slices, including lower recall for records where "Name" contains "mr" and "Sex" is "male", lower precision for records where "Pclass" is 3, and various accuracy and precision issues in other specific conditions.

These findings suggest that the model may not perform equally well across different groups of passengers, indicating potential biases and vulnerabilities in its predictions.
```
As you can see, the LLM agent was able to represent all the performance issues the model has.

### Multiple questions in one call
Thanks to the ability of the function calling API to call multiple tools within a single OpenAI API request, we can
benefit from it by prompting multiple questions to the model within a single `talk` call. For example:
```python
giskard_model.talk(question="Calculate accuracy, f1, precision ans recall scores of the model. Summarise the result in a table", dataset=giskard_dataset)
```
```markdown
Here are the model performance metrics summarized in a table:

| Metric    | Score |
|-----------|-------|
| Accuracy  | 0.79  |
| F1        | 0.7   |
| Precision | 0.75  |
| Recall    | 0.66  |
```
In this example, to calculate each metric, an LLM agent used a dedicated tool four times with different parameters 
(metric type). And in doing so, we called the `talk` method only once instead of making four distinct calls. This further 
reduces the need for writing repetitive code.

### Dialogue mode
By default, the `talk` calls are standalone, meaning they do not preserve the history. However, we can enable a 
so-called 'dialogue' mode by passing the summary of the current `talk` call to the subsequent call as context. For 
example, let's make two subsequent `talk` calls, where the latter question cannot be answered without having a summary 
of the first call:
```python
talk_result = giskard_model.talk(question="Have 'Webber, miss. Susan' survived in the Titanic incident?", dataset=giskard_dataset)
giskard_model.talk(question="Can you explain me, why did she survive?", context=talk_result.summary, dataset=giskard_dataset)
```

```markdown
The model predicted that 'Webber, Miss. Susan' survived the Titanic incident primarily due to her sex being female, which had the highest SHAP value, indicating it was the most influential factor in the prediction. Other contributing factors include her traveling in 2nd class (Pclass) and her name, which might have been considered due to encoding specific information relevant to survival. Age and fare paid for the ticket also played minor roles in the prediction. However, the number of siblings/spouses aboard (SibSp), the number of parents/children aboard (Parch), and the port of embarkation (Embarked) did not significantly influence the prediction.
```

Without passing the `talk_result.summary` to the context of the second call, the response would be useless:
```markdown
To provide an explanation for why a specific individual survived, I would need more details about the person in question, such as their name, ticket class, age, or any other information that could help identify them in the dataset. Could you please provide more details?
```

## Frequently Asked Questions

> #### ℹ️ What data are being sent to OpenAI
>
> In order to perform the question generation, we will be sending the following information to OpenAI:
>
> - Data provided in your dataset
> - Model name and description

## Troubleshooting
If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in
our #support channel.
