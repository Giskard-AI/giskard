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
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```

:::
::::

## 2. Wrap your model

We currently support all **tabular** and **NLP** models from the following:

#### Supported libraries

- sklearn
- catboost
- pytorch
- tensorflow
- huggingface

To create your Giskard model, you can simply wrap your model with `giskard.wrap_model` as shown in {class}`~.giskard.wrap_model`.

:::{warning}
If your ML model contains preprocessing functions (categorical encoding, scaling, etc.), it should be either inside your
`model` or inside the `data_preprocessing_function` of the Giskard model you create.
:::

#### Example

```python
from giskard import wrap_model

wrapped_model = wrap_model(some_classifier,
                           model_type="classification", # or "regression"
                           feature_names=["column1", "column2", ...],
                           classification_labels=["label1", "label2", ...]) # not needed in case of "regression"
```

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

```{eval-rst}
.. autofunction:: giskard.wrap_model 
```

## 3. Wrap your dataset

The Giskard dataset is a wrapper of `pandas.DataFrame`. It contains additional properties like the name of the target
column (ground truth variable), the categorical columns, etc. This object gets passed to the Giskard model (see Create
Giskard model) for evaluation.

:::{warning}
The `pandas.DataFrame` you provide should contain the raw data before prepocessing (categorical encoding, scaling,
etc.).
:::

#### Example

```python
import pandas as pd

# option 1 (preferable)
my_column_types = {"categorical_column": "category",
                   "text_column": "text",
                   "numeric_column": "numeric"}

# option 2 (preferable)                
#my_cat_columns = ["categorical_column"]

# option 3 (not very accurate)
#INFER_CAT_COLUMNS = True

from giskard import wrap_dataset

wrapped_dataset = wrap_dataset(some_df,
                               target="numeric_column",
                               column_types=my_column_types,            # option 1
                               # cat_columns=my_cat_columns,            # option 2
                               # infer_column_types = INFER_CAT_COLUMNS # option 3
                               )
```

```{eval-rst}
.. autofunction:: giskard.wrap_dataset 
```


## 4. Validate your model

To make sure your model is working in Giskard, you can simply execute the following line:

```python
from giskard.core.model_validation import validate_model

validate_model(wrapped_model, wrapped_dataset)
```

## 5. Scan your model for vulnerabilities

Finally 🎉, you can scan your model for vulnerabilities using:
```python
import giskard

results = giskard.scan(wrapped_model, wrapped_dataset, tests=["f1", "accuracy"])

display(results) # in your notebook
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
