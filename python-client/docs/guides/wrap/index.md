# Wrap your ML model and dataset

How to scan your Machine Learning model for vulnerabilities with Giskard?

## Prerequisites

To scan your ML model for vulnerabilities, you need:

- A **model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or even
  any set of *Python* functions.
- A **pandas dataframe** composed of the examples you want to inspect. For example, it could be your test dataset or a
  dataset composed of some wrong predictions of your model.

## Steps to upload your data & model

### 1. Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard library with `pip`:

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

:::{info}
Check our installation guide for more details on the installation procedures.
:::

### 2. Create a Giskard model

We currently support all **tabular** and **NLP** models from the following:

#### Supported libraries

- sklearn
- catboost
- pytorch
- tensorflow
- huggingface

To create your Giskard model, you can either:

1. simply wrap your model with `giskard.wrap_model` as shown in model.
2. or create you own wrapper (if needed) as shown in custom model.

:::{warning}
If your ML model contains preprocessing functions (categorical encoding, scaling, etc.), it should be either inside your
`clf` or inside the `data_preprocessing_function` of the Giskard model you create.
:::

::::{tab-set}
:::{tab-item} model

#### Example

```python
from giskard import wrap_model

my_model = wrap_model(my_model_obj,
                      model_type="classification",
                      feature_names=["column1", "column2", ...],
                      classification_labels=["label1", "label2", ...])
```

:::{info}
Most classes in sklearn and catboost
have [classes_](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html#sklearn.feature_selection.RFE.classes_)
and [feature_names_in_](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html#sklearn.pipeline.Pipeline.feature_names_in_)
as attributes. In these two cases, if you don't
provide us with `classification_labels and feature_names, we will try to infer them
from [classes_](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html#sklearn.feature_selection.RFE.classes_)
and [feature_names_in_](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html#sklearn.pipeline.Pipeline.feature_names_in_)
respectively.
:::

#### Main parameters [Reference]

- `model_obj: the model object. Could be any model from the . The standard model output required for Giskard is:
  - if classification: an array of probabilities corresponding to data entries (rows of pandas.DataFrame) and
    classification_labels. In the case of binary classification, an array of probabilities is also accepted. Make sure
    that the probability provided is for the first label provided in classification_labels.
  - if regression: an array of predictions corresponding to data entries (rows of pandas.DataFrame) and outputs.
- model_type (str):  either classification or regression.
- feature_names (list[str], optional, None): list of feature names matching the column names in the data that
  correspond
  to the features which the model trained on. By default, feature_names are all the Dataset columns except from
  target.
- classification_labels (list, optional, None): that represents the classification labels, if model_type is
  classification. Make sure the labels have the same order as the column output of clf.
- name (str, optional, None): the name of the model.
- classification_threshold (float, optional, 0.5): represents the classification model threshold, for binary
  classification models.
- data_preprocessing_function (Callable[[pandas.DataFrame], any], optional, None): a function that takes a
  pandas.DataFrame as raw input, applies preprocessing and returns any object that could be directly fed to clf. You
  can
  also choose to include your preprocessing inside clf, in which case no need to provide this argument.
- model_postprocessing_function(Callable[any, any], optional, None): a function that takes a clf output as input,
  applies postprocessing and returns an object of the same type and shape as the clf output.

:::

:::{tab-item} Custom mode

#### Example

```python
from giskard import CustomModel


class my_giskard_model(CustomModel):

  # required -- abstractmethod
  def predict_df(self, df: pd.DataFrame):
    """
    Inner method that does the actual inference of a prepared dataframe
    """
    ...


my_model = my_giskard_model(
  name="my_custom_model",
  # clf = my_clf, # not part of CustomModel parameters
  feature_names=my_feature_names,
  model_type="classification",
  classification_labels=my_classification_labels
)
```

:::
::::

### 3. Create a Giskard dataset

The Giskard dataset is a wrapper of `pandas.DataFrame`. It contains additional properties like the name of the target
column (ground truth variable), the categorical columns, etc. This object gets passed to the Giskard model (see Create
Giskard model) for evaluation.

:::{warning}
The `pandas.DataFrame` you provide should contain the raw data before prepocessing (categorical encoding, scaling,
etc.).
:::

::::{tab-set}
:::{tab-item} dataset

#### Example

```python
import pandas as pd

# option 1
my_column_types = {"categorical_column": "category",
                   "text_column": "text",
                   "numeric_column": "numeric"}

# option 2                 
my_cat_columns = ["categorical_column"]

# option 3
INFER_CAT_COLUMNS = True

from giskard import wrap_dataset

my_dataset = wrap_dataset(df=my_df,
                          target="numeric_column",
                          column_types=my_column_types,  # option 1
                          # cat_columns=my_cat_columns,           # option 2
                          # infer_column_types = INFER_CAT_COLUMNS # option 3
                          )
```

#### Description

The Giskard dataset to create from your `pandas.DataFrame.

#### Main parameters [Reference]

:::
::::

### 4. Validate your model

To make sure your model is working in Giskard, you can simply execute the following line:

```python
from giskard.core.model_validation import validate_model

validate_model(my_model, my_dataset)
```

### 5. Upload your model and dataset to giskard UI

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
model_id = my_model.upload(client, "project_key")
dataset_id = my_test_dataset.upload(client, "project_key")
```

### Troubleshooting

If you encounter any issues, join our [Discord](https://discord.gg/fkv7CAr3FE) on our #support channel. Our community
will help! 
