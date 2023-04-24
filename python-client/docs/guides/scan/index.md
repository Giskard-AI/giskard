# 🔬 Scan your ML model

How to scan your Machine Learning model for vulnerabilities with Giskard?

## Prerequisites

To scan your ML model for vulnerabilities, you need:

- A **model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or even
  any set of *Python* functions.
- A **pandas dataframe** composed of the examples you want to inspect. For example, it could be your test dataset or a
  dataset composed of some wrong predictions of your model.

## 1. Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Windows

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/scan#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/scan#subdirectory=python-client"
```

:::
::::

## 2. Wrap your model

We currently support all **tabular** and **NLP** models from `sklearn`, `catboost`, `pytorch`, `tensorflow`
and `huggingface`.

To use your model with Giskard, you can simply wrap your model
with [wrap_model](../../reference/models/index.rst#giskard.wrap_model). The objective of this wrapper is to encapsulate 
the entire prediction process, starting from the **raw** `pandas.DataFrame` and leading up to the final predictions. 

Here's an example:

:::::{tab-set}
::::{tab-item} Classification
:::{important}
Click on [wrap_model](../../reference/models/index.rst#giskard.wrap_model) to see the full documentation.
:::
#### Example

```python
from giskard import wrap_model

# Example of data_preprocessing_function for a pytorch model
# ----------------------------------------------------------
# def my_preprocessing_function(df: pd.DataFrame):
#     return torch.from_numpy(some_scaler.transform(df.to_numpy()))

wrapped_model = wrap_model(model=some_classifier,
                           data_preprocessing_function = None,
                           model_type="classification",
                           feature_names=['sepal length', 'sepal width', 'petal length'],
                           classification_labels=['Setosa', 'Versicolor', 'Virginica'])
```
:::{warning}
If your ML model contains preprocessing functions (categorical encoding, scaling, etc.), it should be either inside your
`model` or inside the `data_preprocessing_function` of the Giskard model you create.
:::

:::{hint}
Most classes in sklearn and catboost
have [classes_](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html#sklearn.feature_selection.RFE.classes_)
and [feature_names_in_](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html#sklearn.pipeline.Pipeline.feature_names_in_)
as attributes. In these two cases, if you don't
provide us with `classification_labels and feature_names, we will try to infer them
from [classes_](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html#sklearn.feature_selection.RFE.classes_)
and [feature_names_in_](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html#sklearn.pipeline.Pipeline.feature_names_in_)
respectively.
:::

::::

::::{tab-item} Regression
:::{important}
Click on [wrap_model](../../reference/models/index.rst#giskard.wrap_model) to see the full documentation.
:::

#### Example
```python
from giskard import wrap_model

wrapped_model = wrap_model(model=some_regressor,
                           model_type="regression",
                           feature_names=['x', 'y', 'z'])
# outputs: Your '<library>' model is successfully wrapped by Giskard's '<wrapper name>' wrapper class.
```
:::{warning}
If your ML model contains preprocessing functions (categorical encoding, scaling, etc.), it should be either inside your
`model` or inside the `data_preprocessing_function` of the Giskard model you create.
:::

::::
:::::

## 3. Wrap your dataset

The Giskard dataset is a wrapper of `pandas.DataFrame`. It contains additional properties like the name of the target
column (ground truth variable), etc. This object gets passed to the Giskard wrapper (
See [Wrap your model](#wrap-your-model)) for evaluation.

:::{important}
Click on [wrap_dataset](../../reference/datasets/index.rst#giskard.wrap_dataset) to see the full documentation.
:::

#### Example
```python
import pandas as pd

iris_df = pd.DataFrame({"sepal length": [5.1],
                        "sepal width": [3.5],
                        "iris_type": ["Setosa"]})

from giskard import wrap_dataset

wrapped_dataset = wrap_dataset(iris_df, target="iris_type")
# outputs: Your 'pandas.DataFrame' dataset is successfully wrapped by Giskard's 'Dataset' wrapper class.
```
:::{warning}
The `pandas.DataFrame` you provide should contain the raw data before prepocessing (categorical encoding, scaling,
etc.). The preprocessing steps should be wrapped in a function that gets assigned to `data_preprocessing_function` of
the [wrap_model](../../reference/models/index.rst#giskard.wrap_model) method.
:::
## 4. Validate your model

To make sure your model is working in Giskard, you can simply execute the following line:

```python
from giskard.core.model_validation import validate_model

validate_model(wrapped_model, wrapped_dataset)
# outputs: Your model is successfully validated.
```

## 5. Scan your model for vulnerabilities

Finally 🎉, you can scan your model for vulnerabilities using:

```python
import giskard

results = giskard.scan(wrapped_model, wrapped_dataset, tests=["f1", "accuracy"])

display(results)  # in your notebook
```

In the notebook, this will produce a widget that allows you to explore the detected issues:
![](<../../assets/scan_results.png>)

You can also get a table of the scan results as a `pandas.DataFrame`. This is useful if you want to save the results of
the scan to a CSV or HTML file.

```python
results_df = results.to_dataframe()
results_df.to_csv("scan_results_my_model.csv")
```  

## 6. Upload your model and dataset to giskard UI

Now that you create your model (in Create a Giskard model) and your data (in Create a Giskard dataset). You can create a
project and upload them to giskard as follows:

```python
from giskard import GiskardClient

# Create a project
url = "http://localhost:19000"
token = "my_API_Access_Token"
client = GiskardClient(url, token)
your_project = client.create_project("project_key", "PROJECT_NAME", "DESCRIPTION")

# Upload your model and dataset
model_id = wrapped_model.upload(client, "project_key")
dataset_id = wrapped_dataset.upload(client, "project_key")
```

## Troubleshooting

If you encounter any issues, join our [Discord](https://discord.gg/fkv7CAr3FE) on our #support channel. Our community
will help! 
