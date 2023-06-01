# 🔬 Scan your ML model

How to scan your Machine Learning model for vulnerabilities with Giskard?

## Prerequisites

To scan your ML model for vulnerabilities, you need:

- A **pandas dataframe** composed of the examples you want to inspect. For example, it could be your test dataset or a
  dataset composed of some wrong predictions of your model.
- A **model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or even
  any set of *Python* functions.

## 1. Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Windows

```sh
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```

:::
::::

## 2. Wrap your dataset

The Giskard dataset is a wrapper of `pandas.DataFrame`. It contains additional properties like the name of the target
column (ground truth variable), etc. This object gets passed to the Giskard model wrapper (
See [Wrap your model](#wrap-your-model)) for evaluation.

The `pandas.DataFrame` you provide should contain the raw data before prepocessing (categorical encoding, scaling,
etc.). The preprocessing steps should be wrapped in a function that gets assigned to `data_preprocessing_function` of
the [wrap_model](../../reference/models/index.rst#giskard.wrap_model) method.

### Usage of [wrap_dataset](../../reference/datasets/index.rst#giskard.wrap_dataset)
```python
import pandas as pd

iris_df = pd.DataFrame({"sepal length": [5.1],
                        "sepal width": [3.5],
                        "size": ["medium"],
                        "species": ["Setosa"]})

from giskard import wrap_dataset

wrapped_dataset = wrap_dataset(
  dataset=iris_df, 
  target="species", # Optional but a MUST if available
  cat_columns=["size"] # Optional but a MUST if available. Inferred automatically if not.
  # name="my_iris_dataset", # Optional
  # column_types=None # # Optional: if not provided, it is inferred automatically
  )
```
* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `dataset`: A `pandas.DataFrame` that contains the raw data (before all the preprocessing steps) and the actual 
     ground truth variable (target).

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `target`: The column name in `dataset` corresponding to the actual target variable (ground truth).
  * `name`: Name of the wrapped dataset.
  * One of:
    * `cat_columns`: A list of strings representing the names of categorical columns. These are columns that are 
       processed by the model with common categorical preprocessing, such as one hot encoding. It can be binary, 
       numerical or textual with few unique values.
       If not provided, the columns types will be automatically inferred.
    * `column_types`: A dictionary of column names and their types (numeric, category or text) for all columns of `dataset`. 
       If not provided, the types will be automatically inferred.

## 3. Wrap your model

We currently support **tabular** and **NLP** models from `sklearn`, `catboost`, `pytorch`, `tensorflow`
and `huggingface`.

To use your model with Giskard, you can simply wrap your model
with [wrap_model](../../reference/models/index.rst#giskard.wrap_model). The objective of this wrapper is to encapsulate 
the entire prediction process, starting from the **raw** `pandas.DataFrame` and leading up to the final predictions. 

If your ML model contains preprocessing functions (categorical encoding, scaling, etc.), it should be either inside your
`model` or inside the `data_preprocessing_function` of the Giskard model you create.

### General usage of [wrap_model](../../reference/models/index.rst#giskard.wrap_model)
:::::::{tab-set}
::::::{tab-item} Classification
```python
from giskard import wrap_model

wrapped_model = wrap_model(
  model=some_classifier,
  model_type="classification",
  classification_labels=['Setosa', 'Versicolor', 'Virginica'],
  # name="my_iris_classification_model", # Optional
  # feature_names=['sepal length', 'sepal width'], # Default: all columns of your dataset
  # classification_threshold=0.5, # Default: 0.5
  # data_preprocessing_function=None, # Optional
  # model_postprocessing_function=None, # Optional
  # **kwargs # Additional model-specific arguments
  )
```
* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow` or `huggingface`.
  * `model_type`: The type of the model, either `regression` or `classification`.
  * `classification_labels`: The list of unique categories contained in your dataset target variable.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your dataset.
  * `classification_threshold`: Model threshold for binary classification problems.
  * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies preprocessing and 
     returns any object that could be directly fed to `model`.
  * `model_postprocessing_function`: A function that takes a `model` output as input, applies postprocessing and returns 
     an object of the same type and shape as the `model` output.
  * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

  ::::::
::::::{tab-item} Regression
```python
from giskard import wrap_model

wrapped_model = wrap_model(
  model=some_regressor,
  model_type="regression",
  # name="my_regression_model", # Optional
  # feature_names=['x', 'y'], # Default: all columns of your dataset
  # data_preprocessing_function=None, # Optional
  # model_postprocessing_function=None, # Optional
  # **kwargs # Additional model-specific arguments
  )
```
* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow` or `huggingface`.
  * `model_type`: The type of the model, either `regression` or `classification`.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your dataset.
  * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies preprocessing and
    returns any object that could be directly fed to `model`.
  * `model_postprocessing_function`: A function that takes a `model` output as input, applies postprocessing and returns
    an object of the same type and shape as the `model` output.
  * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::::
:::::::

### Model-specific [tutorials](../../guides/tutorials/index.md)
:::::{tab-set}
::::{tab-item} sklearn

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

- **<project:../guides/tutorials/sklearn/credit_scoring.md>**
::::

::::{tab-item} catboost

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

- **<project:../guides/tutorials/catboost/credit_scoring.md>**
::::

::::{tab-item} pytorch
- **<project:../guides/tutorials/pytorch/linear_regression.md>**
- **<project:../guides/tutorials/pytorch/sst2_iterable.md>**
- **<project:../guides/tutorials/pytorch/torch_dataset.md>**
- **<project:../guides/tutorials/pytorch/custom_model.md>**
::::

::::{tab-item} tensorflow
- **<project:../guides/tutorials/tensorflow/classification_1d.md>**
- **<project:../guides/tutorials/tensorflow/classification_tfhub.md>**
::::

::::{tab-item} huggingface
- **<project:../guides/tutorials/huggingface/BertForSequenceClassification.md>**
- **<project:../guides/tutorials/huggingface/BertForSequenceClassification_custom.md>**
- **<project:../guides/tutorials/huggingface/pytorch.md>**
- **<project:../guides/tutorials/huggingface/pytorch_pipeline.md>**
- **<project:../guides/tutorials/huggingface/tensorflow.md>**
::::

::::{tab-item} custom wrapper
- **<project:../guides/tutorials/pytorch/custom_model.md>**
- **<project:../guides/tutorials/huggingface/BertForSequenceClassification_custom.md>**
::::
:::::

## 4. Scan your model for vulnerabilities

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

## 5. Upload your model and dataset to giskard UI

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
