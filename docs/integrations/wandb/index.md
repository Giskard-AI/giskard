# Weights and Biases

Weights and Biases, often abbreviated as "wandb," is a platform and toolkit designed for machine learning experimentation 
and collaboration. It provides tools for tracking and visualizing machine learning experiments, managing machine learning 
projects, and sharing results with team members or the broader community. Key features of Weights and Biases include:

- **Experiment Tracking**: Wandb logs hyperparameters, metrics, and visuals for easy experiment comparison and change impact analysis.
- **Visualizations**: Create interactive performance visuals for seamless collaboration and communication.
- **Collaboration**: Wandb facilitates team collaboration by sharing experiments, insights, and results.
- **Model Versioning**: Easily manage and version machine learning models for reproducibility.
- **Hyperparameter Tuning**: Streamline hyperparameter search with wandb to find optimal model configurations.
- **Integration**: Seamlessly incorporate Wandb into your ML workflow, integrating with popular frameworks like TensorFlow and PyTorch.

## Why integrating Giskard?

Giskard offers several compelling reasons to use it in conjunction with Weights and Biases for your machine learning projects:

- **SHAP plot Logging**: Giskard logs SHAP plots into Weights and Biases, aiding feature importance analysis. SHAP plots reveal influential model features.
- **Automated Vulnerability Detection**: Giskard automates the detection of model vulnerabilities, including bias, data leakage, unrobustness, and more. Early detection helps in model development.
- **Customizable Tests**: Giskard generates tailored tests based on detected vulnerabilities. You can further customize these tests by defining domain-specific data slicers and transformers. This flexibility ensures effective model validation and improvement.

## Setup
To use Giskard with Weights and Biases, you need to follow these steps:

1. Setup Weights and Biases:
   - sign up for a Weights and Biases account [here](https://wandb.ai/site).
   - install and open your docker app.
   - install the `wandb` python package and server:
     ```shell
     pip install wandb
     wandb login --relogin # input the API key you get from the website
     wandb server start --upgrade # this will download the docker images if they're not already downloaded
     ```
     
2. Setup Giskard:
   - install the giskard library by following these [instructions](https://docs.giskard.ai/en/latest/guides/installation_library/index.html).

## Logging from Giskard to Weights and Biases
In order to get the most out this integration, you would need to follow these three steps to diagnose your ML model:
- wrap your dataset by following this [guide](https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html).
- wrap your ML model by following this [guide](https://docs.giskard.ai/en/latest/guides/wrap_model/index.html).
- scan your ML model for vulnerabilities by following this [guide](https://docs.giskard.ai/en/latest/guides/scan/index.html).

Once the above steps are done, you can know log the results into Weights and Biases by doing the following:
```python
import giskard, wandb
# [...] wrap model and dataset with giskard
scan_results = giskard.scan(giskard_model, giskard_dataset)
test_suite_results = scan_results.generate_test_suite(use_suite_input=False).run()
shap_results = giskard.explain_with_shap(giskard_model, giskard_dataset)

wandb.login()
giskard_dataset.to_wandb() # log your dataset as a table
scan_results.to_wandb() # log scan results as an HTML report
test_suite_results.to_wandb() # log test suite results as a table
shap_results.to_wandb() # log shap results as plots 
```

```{eval-rst}
.. note:: You can pass to :code:`to_wandb()` all the arguments you can pass to :code:`wandb.init()` (see `here <https://docs.wandb.ai/ref/python/init>`_)
```


## Notebook examples
::::::{grid} 1 1 2 2
:gutter: 1

:::::{grid-item}
:::{card} <br><h3><center>📊 Tabular</center></h3>
:link: wandb-tabular-example.ipynb
:::
:::::
::::::

```{toctree}
:caption: Table of Contents
:name: mastertoc
:maxdepth: 2
:hidden:

wandb-tabular-example
```