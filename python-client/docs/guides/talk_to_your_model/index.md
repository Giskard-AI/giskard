# 🗣️Talk to your model

The **Talk to Your Model** feature allow you to engage in a *conversation* with your model in order to ask him to make
predictions, explain those prediction and help understand those predictions.

To talk to your model, you simply need [to wrap it into giskard](../wrap_model/index.md) and call the `talk` method:

```python
import giskard

giskard_model, giskard_dataset = giskard.demo.titanic_wrapped()

# Create an agent capable of calling your model
import os

os.environ['OPENAI_API_KEY'] = 'sk-...'

from langchain.llms import OpenAI

llm = OpenAI(temperature=0.1)
agent = giskard_model.talk(llm, giskard_dataset, True)

# Query your agent
print(agent.run('Can you tell me if "Webber, Miss. Susan" survived the titanic crash?'))
print(agent.run('Can you explain me why you predicted that "Webber, Miss. Susan" survived the titanic crash?'))
print(agent.run('Is this model reliable?'))
```
