# 🗣️Talk to your model

The **Talk to Your Model** feature allows you to engage in a *conversation* with your ML model. Using natural language, you can:

- Run model predictions.
- Obtain explanations for those predictions, gaining insights into the prediction logic.
- Get decision-making advice based on the prediction.

## Making predictions

To talk to your model, you simply need [to wrap it with giskard](../wrap_model/index.md) and call the `talk` method:

```python
import giskard
import os

# Running this with our demo model and dataset for Titanic survival prediction
model, df = giskard.demo.titanic()
giskard_dataset = giskard.Dataset(df=df, target="Survived", name="Titanic dataset")
giskard_model = giskard.Model(model=model, model_type="classification",
                              name="Titanic model that returns yes if survived otherwise no",
                              classification_labels=["no", "yes"])

# Set your OpenAI API key, by default we are using GPT 3.5
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Talk to your model
print(giskard_model.talk('What is this model doing?'))
# -> This model is a Titanic model that returns yes or no if the passenger survived.

print(giskard_model.talk('Can you tell me if "Webber, Miss. Susan" survived the titanic crash?', giskard_dataset, True))
# -> Yes, "Webber, Miss. Susan" survived the titanic crash.


print(giskard_model.talk('Can you explain to me why you predicted that "Webber, Miss. Susan" survived the titanic crash? Which feature was important?', giskard_dataset, True))
# -> 
```

## Asking questions about reliability

To ask questions about the model's reliability, you can provide results from the Giskard scan to the `talk` method:

```python
import giskard
import os

# Running this with our demo model and dataset for Titanic survival prediction
model, df = giskard.demo.titanic()
giskard_dataset = giskard.Dataset(df=df, target="Survived", name="Titanic dataset")
giskard_model = giskard.Model(model=model, model_type="classification",
                              name="Titanic model that return yes if survived otherwise no",
                              classification_labels=['no', 'yes'])

# Scan your model
scan_result = giskard.scan(giskard_model, giskard_dataset)

# Set up your OpenAI API key, by default we are using GPT 3.5
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Talk to your model
print(giskard_model.talk("Is this model reliable?", scan_result=scan_result))
# -> The model is not reliable.

print(giskard_model.talk("Can I trust this model?", scan_result=scan_result))
# -> No, this model is not reliable due to its vulnerabilities and overconfidence issues.

print(giskard_model.talk("What are the risks of this model?", scan_result=scan_result))
# -> The risks associated with this model are: not reliable, performance issues with Name containing "mr", Sex being "male", Pclass being 3, Name containing "master", Embarked being "S", Pclass being 1, Name containing "miss", Embarked being "Q", robustness issues, overconfidence issues, and spurious correlation issues.

print(giskard_model.talk("How good is the quality of this model?", scan_result=scan_result))
# -> The model is not reliable and has several vulnerabilities.

print(giskard_model.talk("Was this model well built?", scan_result=scan_result))
# -> No, this model was not well built as it has several vulnerabilities and reliability issues.

print(giskard_model.talk("Are there any vulnerabilities in this model?", scan_result=scan_result))
# -> Yes, there are some vulnerabilities in this model.

print(giskard_model.talk("What are the vulnerabilities of this model?", scan_result=scan_result))
# -> The vulnerabilities of the model are: \n<PerformanceIssue slice=\'`Name` contains "mr"\', metric=\'Recall\', metric_delta=-96.85%>: 264 samples (59.19%)\n<PerformanceIssue slice=\'`Sex` == "male"\', metric=\'Recall\', metric_delta=-83.19%>: 296 samples (66.37%)\n<PerformanceIssue slice=\'`Pclass` == 3\', metric=\'Precision\', metric_delta=-36.89%>: 247 samples (55.38%)\n<PerformanceIssue slice=\'`Name` contains "master"\', metric=\'Accuracy\', metric_delta=-10.00%>: 24 samples (5.38%)\n<PerformanceIssue slice=\'`Embarked` == "S"\', metric=\'Recall\', metric_delta=-7.52%>: 317 samples (71.08%)\n<PerformanceIssue slice=\'`Pclass` == 1\', metric=\'Accuracy\', metric_delta=-6.82%>: 105 samples (23.54%)\n<PerformanceIssue slice=\'`Name` contains "miss"\', metric=\'Accuracy\', metric

```

## Go from simple predictions to decision-making

```python
import giskard
import os

# Running this with our demo model and dataset for Titanic survival prediction
model, df = giskard.demo.titanic()
giskard_dataset = giskard.Dataset(df=df, target="Survived", name="Titanic dataset")
giskard_model = giskard.Model(model=model, model_type="classification",
                              name="Titanic model that returns yes if survived otherwise no",
                              classification_labels=["no", "yes"])

# Set your OpenAI API key, by default we are using GPT 3.5
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Talk to your model
print(giskard_model.talk("I'm making a movie about the Titanic. What characteristics should the main character possess to ensure their survival?"))
# -> 
```

## Use a custom language model

By default, GPT 3.5 will be used to generate responses. You can make use of
your preferred [large language model](https://python.langchain.com/docs/modules/model_io/models/) by setting the default llm globally
using `giskard.set_default_llm`:

```python
import giskard
from langchain.llms import Cohere

# Create your llm
llm = Cohere()

# Set your llm globally
giskard.llm_config.set_default_llm(llm)
```

