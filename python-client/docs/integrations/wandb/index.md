# Weights and Biases

Weights and Biases, often abbreviated as "wandb," is a platform and toolkit designed for machine learning experimentation 
and collaboration. It provides tools for tracking and visualizing machine learning experiments, managing machine learning 
projects, and sharing results with team members or the broader community. Key features of Weights and Biases include:

- **Experiment Tracking**: Wandb allows you to log and track various aspects of your machine learning experiments, such as hyperparameters, model performance metrics, and visualizations. This helps you keep a record of your experiments, compare different runs, and understand the impact of various changes on your models.
- **Visualizations**: You can create interactive visualizations of your model's performance, which can be shared with others to facilitate collaboration and communication.
- **Collaboration**: Teams can use Weights and Biases to work together on machine learning projects. It provides tools for sharing experiments, insights, and results, making it easier for team members to collaborate effectively.
- **Model Versioning**: Weights and Biases helps you manage and version your machine learning models, making it easier to track changes and reproduce results.
- **Hyperparameter Tuning**: You can use wandb for hyperparameter tuning, allowing you to systematically search for the best combination of hyperparameters for your models.
- **Integration**: Weights and Biases integrates with popular machine learning frameworks like TensorFlow, PyTorch, and scikit-learn, making it easy to incorporate into your existing workflows.

## Why integrating Giskard?

Giskard offers several compelling reasons to use it in conjunction with Weights and Biases for your machine learning projects:

- **Feature Importance Analysis with SHAP Plots**: Giskard provides the capability to log SHAP (SHapley Additive exPlanations) plots into Weights and Biases. SHAP plots are a powerful tool for understanding the impact of individual features on your model's predictions. They help you identify which features are most influential in your model's decision-making process. By logging SHAP plots, Giskard enables you to gain deeper insights into your model's behavior and feature importance.
- **Automated Vulnerability Detection**: Giskard's scan feature is designed to automatically detect various vulnerabilities in your machine learning models. These vulnerabilities can include performance bias (where the model favors certain groups or classes), data leakage (inadvertently using information from the test set during training), unrobustness (sensitivity to small changes in input data), spurious correlation (false relationships between features and outcomes), overconfidence, underconfidence, and even ethical issues. This automated vulnerability detection helps you identify potential problems in your models early in the development process.
- **Customizable Domain-Specific Tests**: Giskard goes beyond just identifying vulnerabilities; it also helps you take action by generating relevant tests based on the vulnerabilities it detects. These tests are tailored to address the specific issues found in your model. What's even more valuable is that Giskard allows you to customize these tests further to suit your specific use case. You can define domain-specific data slicers and transformers as fixtures of your test suites, ensuring that the generated tests align with your project's unique requirements. This level of customization ensures that you can effectively validate and improve your models.

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
test_suite_results = scan_results.generate_test_suite().run()
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