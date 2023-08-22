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
print(giskard_model.talk('Can you tell me if "Webber, Miss. Susan" survived the titanic crash?', giskard_dataset, True))
print(giskard_model.talk('Can you explain me why you predicted that "Webber, Miss. Susan" survived the titanic crash?',
                         giskard_dataset, True))
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

