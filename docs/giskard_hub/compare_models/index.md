# ⚖️ Compare models

Comparing different models enables you to:
* At prototyping time, **choose the best model** among various candidates with different LLM prompts, LLM providers, hyperparameters, etc.
* At production time, decide whether to **promote** a new model version over the running model in production.

Building a great test suite is key to being able to compare models. With Giskard, you can:
* Run the same test suite for different **models**: this is useful for comparing different models.
* Run the same test suite for different **datasets**: this is useful for monitoring your model with different batches of examples.

![Comparison](../../assets/comparison.png)

➡️ To compare models or datasets with the same test suite, just click on the compare button after creating a test suite.

> 💡 Try it live with our Hugging Face space: [here](https://giskardai-giskard.hf.space/main/projects)

## Expose an input to allow comparison

Comparison require you to expose at least an input to your test suite.

In order to expose a test input, perform the following steps:

- Click the **Edit parameters** button
- Change the input that you want to expose from **Fixed value** to **Suite input**
- Click the **Save** button

We recommend you to always have **all** your tests exposing their **models** and **datasets** inputs

