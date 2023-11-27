# 🏃 MLflow
**Automatically evaluate your ML models with MLflow's evaluation API and Giskard as a plugin.**
```{toctree}
:caption: Table of Contents
:maxdepth: 1
:hidden:

./mlflow-llm-example.ipynb
./mlflow-tabular-example.ipynb

```

## Why MLflow?

MLflow is an open-source platform for managing end-to-end machine learning (ML) workflows. It was developed by Databricks and has gained popularity in the machine learning community for its versatility and ease of use. MLflow provides a set of tools and functionalities that help data scientists and machine learning engineers with the following aspects of the ML development process:

- **Experiment Tracking**: Log and track ML experiments.
- **Code Packaging**: Easily package ML code for reproducibility.
- **Model Versioning**: Keep track of different model versions.
- **Model Deployment**: Integrate with deployment platforms.
- **UI and Community**: User-friendly UI with broad community support.

## Why integrating Giskard?

Integrating Giskard with MLflow offers several compelling advantages for managing and enhancing machine learning workflows:
- **Seamless Integration with `mlflow.evaluate()`**: Giskard effortlessly integrates with MLflow's evaluation API, simplifying vulnerability assessment.
- **Automated Vulnerability Detection**: Giskard's scan feature ensures the identification of hidden vulnerabilities in ML models by generating a comprehensive report that can be logged into MLflow.
  - **Tabular and NLP models**: wherein some of the most important vulnerabilities revolves around **performance biases**, **data leakage**, **unrobustness**, and more.
  - **LLMs**: wherein some of the most critical vulnerabilities are **Prompt Injection** (when LLMs are manipulated to behave as the attacker wishes), **Sensitive Information Disclosure** (when LLMs inadvertently leak confidential information), **Hallucination** (when LLMs generate inaccurate or inappropriate content), and more.
- **Customizable Tests**: Giskard generates tailored tests based on the detected vulnerabilities. You can further customize these tests by defining domain-specific data slicers and transformers.
- **Enhanced Model Governance**: This integration supports transparent model evaluation and governance, crucial for meeting best practices and compliance requirements.

## MLflow's `evaluate` API and the Giskard plugin
In order to use the plugin, you would first need to:

- Install `mlflow` to access to the [`mlflow.evaluate()` API](https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.evaluate).
- Install `giskard` (follow these [instructions](https://docs.giskard.ai/en/latest/open_source/installation_library/index.html))
  to access to the [`giskard` evaluator](https://mlflow.org/docs/latest/plugins.html#model-evaluation-plugins).

After completing the installation process, you will be able to observe giskard as part of mlflow’s evaluators:

```python
import mlflow
mlflow.models.list_evaluators() # ['default', 'giskard']
```

The configuration of the giskard evaluator can be done entirely through the `evaluator_config` argument that can yield 3 keys:

- `model_config`: to be filled according to our [guides](https://docs.giskard.ai/en/latest/open_source/scan/index.html) with the help of our [model API reference](https://docs.giskard.ai/en/latest/reference/models/index.html).
- `dataset_config`: to be filled according to our [guides](https://docs.giskard.ai/en/latest/open_source/scan/index.html) with the help of our [dataset API reference](https://docs.giskard.ai/en/latest/reference/datasets/index.html).
- `scan_config`: to be filled according to our [guides](https://docs.giskard.ai/en/latest/open_source/scan/index.html) with the help of our [scan API reference](https://docs.giskard.ai/en/latest/reference/scan/index.html).

Here's the integration in a nutshell:
```python
evaluator_config = {"model_config":   {"classification_labels": ["no", "yes"]},
                    "dataset_config": {"name": "Articles"},
                    "scan_config":    {"params": {"text_perturbation": {"num_samples": 1000}}}}

with mlflow.start_run(run_name="my_run") as run:
  model_uri = mlflow.sklearn.log_model(..., pyfunc_predict_fn="predict_proba").model_uri
  mlflow.evaluate(model=model_uri,
                  model_type="classifier",
                  data=df_sample,
                  evaluators="giskard",
                  evaluator_config=evaluator_config)
```
:::{hint}
- **Data preprocessing**: In order to include your data preprocessing into the prediction pipeline, you should log a [custom python model](https://www.mlflow.org/docs/latest/models.html#custom-python-models) with MLflow.
- **`sklearn` models**: we strongly recommend to `log_model` with `pyfunc_predict_fn="predict_proba"` in order to get the best out of the evaluation.
:::
For more complete examples, check our notebook examples below.

## Notebook examples
::::::{grid} 1 1 2 2
:gutter: 1

:::::{grid-item}
:::{card} <br><h3><center>📊 Tabular</center></h3>
:link: mlflow-tabular-example.ipynb
:::
:::::

:::::{grid-item}
:::{card} <br><h3><center>📝 LLM</center></h3>
:link: mlflow-llm-example.ipynb
:::
:::::
::::::

## Logging giskard objects to MLflow
It is possible to log 4 giskard objects into MLflow:

- A giskard [dataset](https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html)
- A giskard [model](https://docs.giskard.ai/en/latest/guides/wrap_model/index.html)
- The [scan](https://docs.giskard.ai/en/latest/guides/scan/index.html) results
- The [test-suite](https://docs.giskard.ai/en/latest/guides/scan/index.html) results

Here are two options on how to achieve this.

### Option 1 (via the fluent API)
```python
import mlflow

with mlflow.start_run() as run:
    giskard_model.to_mlflow()
    giskard_dataset.to_mlflow()
    scan_results.to_mlflow()
    test_suite_results.to_mlflow()
```

### Option 2 (via MlflowClient)
```python
from mlflow import MlflowClient

client = MlflowClient()
experiment_id = "0"
run = client.create_run(experiment_id)

giskard_model.to_mlflow(client, run.info.run_id)
giskard_dataset.to_mlflow(client, run.info.run_id)
scan_results.to_mlflow(client, run.info.run_id)
test_suite_results.to_mlflow(client, run.info.run_id)
```
