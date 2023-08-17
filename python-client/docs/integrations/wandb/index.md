# Weights and Biases

Logging SHAP plots, scan reports and test suites into Weights & Biases is now possible with Giskard that enables you to:
- **Understand feature importance**: Giskard generates plots to highlight feature importance using the SHAP library.
- **Scan your model to find dozens of hidden vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfidence, underconfidence, unethical issue, etc.
- **Instantaneously generate domain-specific tests**: Giskard automatically generates relevant tests based on the vulnerabilities detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slicers and transformers as fixtures of your test suites.

## Setup
To use Giskard with Weights & Biases, you need to follow these steps:

1. Setup Weights & Biases:
   - sign up for a Weights & Biases account [here](https://wandb.ai/site).
   - install and open your docker app.
   - install the `wandb` python package and server:
     ```shell
     pip install wandb
     wandb login --relogin # input the API key you get from the website
     wandb server start --upgrade # this will download the docker images if they're not already downloaded
     ```
     
2. Setup Giskard:
   - install the giskard library by following these [instructions](https://docs.giskard.ai/en/latest/guides/installation_library/index.html).

## Logging from Giskard to Weights & Biases
In order to get the most out this integration, you would need to follow these three steps to diagnose your ML model:
- wrap your dataset by following this [guide](https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html).
- wrap your ML model by following this [guide](https://docs.giskard.ai/en/latest/guides/wrap_model/index.html).
- scan your ML model for vulnerabilities by following this [guide](https://docs.giskard.ai/en/latest/guides/scan/index.html).

Once the above steps are done, you can know log the results into Weights & Biases by doing the following:
```python
import giskard, wandb
# [...] wrap model and dataset with giskard
scan_results = giskard.scan(giskard_model, giskard_dataset)
test_suite_results = scan_results.generate_test_suite().run()

wandb.login()
giskard_dataset.to_wandb() # log your dataset as a table
scan_results.to_wandb() # log scan results as an HTML report
test_suite_results.to_wandb() # log test suite results as a table
# TODO: log SHAP plots
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