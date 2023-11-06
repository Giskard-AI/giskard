# ⚖️ Compare models

Comparing different models enables you to:
* At prototyping time, **choose the best model** amongst various candidates with different LLM prompts, LLM providers, hyperparameters, etc.
* At production time, decide to **promote** a new model version against the running model in production

Building great test suite is key to be able to compare models. With Giskard, you can:
* Run the same test suite for different **models**: this is useful to compare different models
* Run the same test suite for different **datasets**: this useful to monitor your model with different batch of examples

![Comparison](../../assets/comparison.png)

➡️ To compare models or datasets with the same test suite, just click on compare button after creating a test suite.

> 💡 Try in live with our Hugging Face space: [here](https://giskardai-giskard.hf.space/main/projects)