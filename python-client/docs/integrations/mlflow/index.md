# MLflow

MLflow is an open-source platform for managing end-to-end machine learning (ML) workflows. 
It was developed by Databricks and has gained popularity in the machine learning community for its versatility and ease of use. 
MLflow provides a set of tools and functionalities that help data scientists and machine learning engineers with the 
following aspects of the ML development process:

- **Experiment Tracking**: Log and track ML experiments.
- **Code Packaging**: Easily package ML code for reproducibility.
- **Model Versioning**: Keep track of different model versions.
- **Model Deployment**: Integrate with deployment platforms.
- **UI and Community**: User-friendly UI with broad community support.

## Why integrating Giskard?

Integrating Giskard with MLflow offers several compelling advantages for managing and enhancing machine learning workflows:
- **Seamless Integration with `mlflow.evaluate()`**: Giskard effortlessly integrates with MLflow's evaluation API, simplifying vulnerability assessment.
- **Comprehensive Vulnerability Reports**: Giskard's [scans](https://docs.giskard.ai/en/latest/guides/scan/index.html) cover performance bias, data leakage, model robustness, and more, providing in-depth model assessments.
- **Efficient Metric Logging**: Easily track and compare model performance, robustness, and ethical considerations within MLflow.
- **Enhanced Model Governance**: This integration supports transparent model evaluation and governance, crucial for meeting best practices and compliance requirements.

## Setup
The following requirements are necessary to use the plug-in:

- Install `mlflow` to access to the `mlflow.evaluate()` API.
- Install `giskard` (follow these [instructions](https://docs.giskard.ai/en/latest/guides/installation_library/index.html))
  to access to the `giskard` evaluator.

After completing the installation process, you will be able to observe giskard as part of mlflow’s evaluators:

```python
import mlflow
mlflow.models.list_evaluators() # ['default', 'giskard']
```

## Notebook examples
::::::{grid} 1 1 2 2
:gutter: 1

:::::{grid-item}
:::{card} <br><h3><center>📊 Tabular</center></h3>
:link: mlflow-tabular-example.ipynb
:::
:::::

:::::{grid-item}
:::{card} <br><h3><center>📝 Text</center></h3>
:link: mlflow-llm-example.ipynb
:::
:::::
::::::

## Plug-in parameters

The configuration of the giskard evaluator can be done entirely through the `evaluator_config` argument that can yield 3 keys:

- `model_config`: to be filled according to this [page](https://docs.giskard.ai/en/latest/reference/models/index.html).
- `dataset_config`: to be filled according to this [page](https://docs.giskard.ai/en/latest/reference/datasets/index.html).
- `scan_config`: to be filled according to this [page](https://docs.giskard.ai/en/latest/reference/scan/index.html).

As an example:
```python
evaluator_config = {"model_config":   {"classification_labels": ["no", "yes"]},
                    "dataset_config": {"name": "Articles"},
                    "scan_config":    {"params": {"text_perturbation": {"num_samples": 1000}}}}
mlflow.evaluate(model=model_uri,
                model_type="classifier",
                data=df_sample,
                evaluators="giskard",
                evaluator_config=evaluator_config)
```

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

```{toctree}
:caption: Table of Contents
:name: mastertoc
:maxdepth: 2
:hidden:

mlflow-tabular-example
mlflow-llm-example
```