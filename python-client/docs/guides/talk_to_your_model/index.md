# 🗣️Talk to your model

The **Talk to Your Model** feature allow you to engage in a *conversation* with your model in order to ask him to make
predictions, explain those prediction and help understand those predictions.

To talk to your model, you simply need [to wrap it into giskard](../wrap_model/index.md) and call the `talk` method:

```python
import giskard
import os

model, df = giskard.demo.titanic()
giskard_dataset = giskard.Dataset(df=df, target="Survived", name="Titanic dataset")
giskard_model = giskard.Model(model=model, model_type="classification",
                              name="Titanic model that return yes if survived otherwise no",
                              classification_labels=['no', 'yes'])

# Set up your OpenAI API key, by default we are using GPT 3.5
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Talk to your model
print(giskard_model.talk('What is this model doing?'))
# -> This model is a Titanic model that returns yes or no if the passenger survived.

print(giskard_model.talk('Can you tell me if "Webber, Miss. Susan" survived the titanic crash?', giskard_dataset, True))
# -> Yes, "Webber, Miss. Susan" survived the titanic crash.


print(giskard_model.talk(
    'Can you explain me why you predicted that "Webber, Miss. Susan" survived the titanic crash? What feature was important?',
                         giskard_dataset, True))
# -> 
```

## Asking question about reliability

You can provide the scan result to the `talk` method in order to ask question related to reliability:

```python
import giskard
import os

model, df = giskard.demo.titanic()
giskard_dataset = giskard.Dataset(df=df, target="Survived", name="Titanic dataset")
giskard_model = giskard.Model(model=model, model_type="classification",
                              name="Titanic model that return yes if survived otherwise no",
                              classification_labels=['no', 'yes'])

# scan your model
scan_result = giskard.scan(giskard_model, giskard_dataset)

# Set up your OpenAI API key, by default we are using GPT 3.5
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Talk to your model
print(giskard_model.talk("Is this model reliable?", scan_result=scan_result))
# -> The model is not reliable.

print(giskard_model.talk("Can I trust this model?", scan_result=scan_result))
# -> No, this model is not reliable due to its vulnerabilities and overconfidence issues.

print(giskard_model.talk("What are the risk of this model?", scan_result=scan_result))
# -> The risks associated with this model are: not reliable, performance issues with Name containing "mr", Sex being "male", Pclass being 3, Name containing "master", Embarked being "S", Pclass being 1, Name containing "miss", Embarked being "Q", robustness issues, overconfidence issues, and spurious correlation issues.

print(giskard_model.talk("How quality is this model?", scan_result=scan_result))
# -> The model is not reliable and has several vulnerabilities.

print(giskard_model.talk("Was this model well build?", scan_result=scan_result))
# -> No, this model was not well built as it has several vulnerabilities and reliability issues.

print(giskard_model.talk("Is there any vulnerability in this model?", scan_result=scan_result))
# -> Yes, there are some vulnerabilities in this model.

print(giskard_model.talk("What are the vulnerabilities of this model?", scan_result=scan_result))
# -> The vulnerabilities of the model are: \n<PerformanceIssue slice=\'`Name` contains "mr"\', metric=\'Recall\', metric_delta=-96.85%>: 264 samples (59.19%)\n<PerformanceIssue slice=\'`Sex` == "male"\', metric=\'Recall\', metric_delta=-83.19%>: 296 samples (66.37%)\n<PerformanceIssue slice=\'`Pclass` == 3\', metric=\'Precision\', metric_delta=-36.89%>: 247 samples (55.38%)\n<PerformanceIssue slice=\'`Name` contains "master"\', metric=\'Accuracy\', metric_delta=-10.00%>: 24 samples (5.38%)\n<PerformanceIssue slice=\'`Embarked` == "S"\', metric=\'Recall\', metric_delta=-7.52%>: 317 samples (71.08%)\n<PerformanceIssue slice=\'`Pclass` == 1\', metric=\'Accuracy\', metric_delta=-6.82%>: 105 samples (23.54%)\n<PerformanceIssue slice=\'`Name` contains "miss"\', metric=\'Accuracy\', metric



```

## Using a custom language model

By default, GPT 3.5 will be used to generate response. You can use
any [language model](https://python.langchain.com/docs/modules/model_io/models/) by setting the default llm globally
using `giskard.set_default_llm`:

```python
import giskard
from langchain.llms import Cohere

# Create your llm
llm = Cohere()

# Set your llm globally
giskard.llm_config.set_default_llm(llm)
```

