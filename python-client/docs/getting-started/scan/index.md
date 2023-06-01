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
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```

:::
::::

## 2. Wrap your dataset

The Giskard dataset is a wrapper of `pandas.DataFrame`. It contains additional properties like the name of the target
column (ground truth variable), etc. This object gets passed to the Giskard model wrapper (
See [Wrap your model](#wrap-your-model)) for evaluation.

The `pandas.DataFrame` you provide should contain the raw data before prepocessing (categorical encoding, scaling,
etc.).

```python
import pandas as pd

iris_df = pd.DataFrame({"sepal length": [5.1],
                        "sepal width": [3.5],
                        "petal size": ["medium"],
                        "species": ["Setosa"]})

from giskard import Dataset

wrapped_dataset = Dataset(
  df=iris_df,
  target="species",  # Optional but a MUST if available
  cat_columns=["petal size"]  # Optional but a MUST if available. Inferred automatically if not.
  # name="my_iris_dataset", # Optional
  # column_types=None # # Optional: if not provided, it is inferred automatically
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `df`: A `pandas.DataFrame` that contains the raw data (before all the preprocessing steps) and the actual
    ground truth variable (target). `df` can contain more columns than the features of the model such as the sample_id,
    metadata, etc.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `target`: The column name in `dataset` corresponding to the actual target variable (ground truth).
  * `name`: Name of the wrapped dataset.
  * One of:
    * `cat_columns`: A list of strings representing the names of categorical columns. These are columns that are
      processed by the model with common categorical preprocessing, such as one hot encoding. It can be binary,
      numerical or textual with few unique values.
      If not provided, the columns types will be automatically inferred.
    * `column_types`: A dictionary of column names and their types (numeric, category or text) for all columns
      of `dataset`.
      If not provided, the types will be automatically inferred.

## 3. Wrap your model

To use your model with Giskard, you can either:

- <b> Wrap a prediction function</b> that contains all your data preprocessing steps.
- <b> Wrap a model object</b> in addition to a data preprocessing function.

:::{hint}
Choose <b>"Wrap a model object"</b> if your model is not serializable by `cloudpickle` (e.g. TensorFlow models).
:::

:::::::{tab-set}
::::::{tab-item} Wrap a prediction function
:::::{tab-set}
::::{tab-item} Classification
Prediction function is any Python function that takes as input the <b>raw</b> pandas dataframe (wrapped in the
[previous section](#wrap-your-dataset)) and returns the <b>probabilities</b> for each classification labels.

<b><u>Make sure that:</b></u>

1. `prediction_function` encapsulates all the <b>data preprocessing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from giskard import Model

scaler = StandardScaler()
clf = LogisticRegression()


def prediction_function(df: pd.DataFrame) -> np.ndarray:
  # Scale all the numerical variables
  num_cols = ["sepal length", "sepal width"]
  df[num_cols] = scaler.transform(df[num_cols])

  return clf.predict_proba(df)


wrapped_model = Model(
  prediction_function,
  model_type="classification",
  classification_labels=['Setosa', 'Versicolor', 'Virginica'], # Their order MUST be identical to the prediction_function's output order
  feature_names=['sepal length', 'sepal width'],  # Default: all columns of your dataset
  # name="my_iris_classification_model", # Optional
  # classification_threshold=0.5, # Default: 0.5
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns an array ($n\times m$) of
    probabilities corresponding
    to $n$ data entries (rows of `pandas.DataFrame`) and $m$ `classification_labels`. In the case of binary
    classification, an array  
    ($n\times 1$) of probabilities is also accepted.
  * `model_type`: The type of the model, either `regression` or `classification`.
  * `classification_labels`: The list of unique categories contained in your dataset target variable.
    If `classification_labels`
    is a list of $m$ elements, make sure that:
    * `prediction_function` is returning a ($n\times m$) array of probabilities.
    * `classification_labels` have the same order as the output of `prediction_function`.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
    dataset.
    Make sure these features have the same order as in your training dataset.
  * `classification_threshold`: Model threshold for binary classification problems.

::::
::::{tab-item} Regression
Prediction function is any Python function that takes as input the <b>raw</b> pandas dataframe (wrapped in the
[previous section](#wrap-your-dataset)) and returns the <b>predictions</b> for your regression task.

<b><u>Make sure that:</b></u>

1. `prediction_function` encapsulates all the <b>data preprocessing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from giskard import Model

reg = LinearRegression()


def prediction_function(df: pd.DataFrame) -> np.ndarray:
  df['x'] = df['x'] * 2
  return reg.predict(df)


wrapped_model = Model(
  prediction_function,
  model_type="regression",
  feature_names=['x', 'y'],  # Default: all columns of your dataset
  # name="my_regression_model", # Optional
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns an array $n$ of predictions
    corresponding
    to $n$ data entries (rows of `pandas.DataFrame`).
  * `model_type`: The type of the model, either `regression` or `classification`.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
    dataset.
    Make sure these features have the same order as in your training dataset.

::::
:::::
::::::
::::::{tab-item} Wrap a model object
Providing the model object to `Model` allows us to automatically infer the ML library of your `model`
object and provide a suitable serialization method (provided by `save_model` and `load_model` methods).

This requires:

- <b><u>Mandatory</u></b>: Overriding the `model_predict` method which should take as input the <b>raw</b> pandas dataframe 
  and returns the <b>probabilities</b> for each classification labels (classification) or predictions (regression).
- <b><u>Optional</u></b>: Our pre-defined serialization and prediction methods cover the `sklearn`, `catboost`, `pytorch`,
   `tensorflow` and `huggingface` libraries. If none of these libraries are detected, `cloudpickle`
   is used as default for serialization. If this fails, we will ask you to also override the `save_model` and `load_model`
   methods where you provide your own serialization of the `model` object.

:::::{tab-set}
::::{tab-item} Classification

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from giskard import Model

scaler = StandardScaler()
clf = LogisticRegression()


class MyCustomModel(Model):
  def model_predict(self, df: pd.DataFrame):
    num_cols = ["sepal length", "sepal width"]
    df[num_cols] = scaler.transform(df[num_cols])
    return self.model.predict_proba(df)


wrapped_model = MyCustomModel(
  model=clf,
  model_type="classification",
  classification_labels=['Setosa', 'Versicolor', 'Virginica'] # Their order MUST be identical to the prediction_function's output order
  # name="my_iris_classification_model", # Optional
  # classification_threshold=0.5, # Default: 0.5
  # model_postprocessing_function=None, # Optional
  # **kwargs # Additional model-specific arguments
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow` or `huggingface` (check
    the [tutorials](../../guides/tutorials/index.md)). If none of these
    libraries apply to you, we try to serialize your model with `cloudpickle`, if that also does not work, we
    ask you to provide us with your own serialization method.
  * `model_type`: The type of the model, either `regression` or `classification`.
  * `classification_labels`: The list of unique categories contained in your dataset target variable.
    If `classification_labels`
    is a list of $m$ elements, make sure that:
    * `prediction_function` is returning a ($n\times m$) array of probabilities.
    * `classification_labels` have the same order as the output of `prediction_function`.


* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
    dataset.
    Make sure these features have the same order as in your training dataset.
  * `classification_threshold`: Model threshold for binary classification problems.
  * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies preprocessing and
    returns any object that could be directly fed to `model`.
  * `model_postprocessing_function`: A function that takes a `model` output as input, applies postprocessing and returns
    an object of the same type and shape as the `model` output.
  * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::
::::{tab-item} Regression

```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from giskard import Model

reg = LinearRegression()


class MyCustomModel(Model):
  def model_predict(self, df: pd.DataFrame):
    df['x'] = df['x'] * 2
    return self.model.predict(df)


wrapped_model = MyCustomModel(
  model=reg,
  model_type="regression",
  feature_names=['x', 'y'],  # Default: all columns of your dataset
  # name="my_regression_model", # Optional
  # model_postprocessing_function=None, # Optional
  # **kwargs # Additional model-specific arguments
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
  * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow` or `huggingface` (check
    the [tutorials](../../guides/tutorials/index.md)). If none of these
    libraries apply to you, we try to serialize your model with `cloudpickle`, if that also does not work, we
    ask you to provide us with your own serialization method.
  * `model_type`: The type of the model, either `regression` or `classification`.

* <mark style="color:red;">**`Optional parameters`**</mark>
  * `name`: Name of the wrapped model.
  * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
    dataset.
    Make sure these features have the same order as in your training dataset.
  * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies preprocessing and
    returns any object that could be directly fed to `model`.
  * `model_postprocessing_function`: A function that takes a `model` output as input, applies postprocessing and returns
    an object of the same type and shape as the `model` output.
  * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::
:::::
::::::
:::::::

### Model-specific [tutorials](../../guides/tutorials/index.md)

:::::{tab-set}
::::{tab-item} Any function

- **<project:../../guides/tutorials/pytorch/custom_model.md>**
- **<project:../../guides/tutorials/huggingface/BertForSequenceClassification_custom.md>**
  ::::

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

- **<project:../../guides/tutorials/sklearn/credit_scoring.md>**
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

- **<project:../../guides/tutorials/catboost/credit_scoring.md>**
  ::::

::::{tab-item} pytorch

- **<project:../../guides/tutorials/pytorch/linear_regression.md>**
- **<project:../../guides/tutorials/pytorch/sst2_iterable.md>**
- **<project:../../guides/tutorials/pytorch/torch_dataset.md>**
- **<project:../../guides/tutorials/pytorch/custom_model.md>**
  ::::

::::{tab-item} tensorflow

- **<project:../../guides/tutorials/tensorflow/classification_1d.md>**
- **<project:../../guides/tutorials/tensorflow/classification_tfhub.md>**
  ::::

::::{tab-item} huggingface

- **<project:../../guides/tutorials/huggingface/BertForSequenceClassification.md>**
- **<project:../../guides/tutorials/huggingface/BertForSequenceClassification_custom.md>**
- **<project:../../guides/tutorials/huggingface/pytorch.md>**
- **<project:../../guides/tutorials/huggingface/pytorch_pipeline.md>**
- **<project:../../guides/tutorials/huggingface/tensorflow.md>**
  ::::
  :::::

## 4. Scan your model for vulnerabilities

Finally 🎉, you can scan your model for vulnerabilities using:

```python
import giskard

results = giskard.scan(wrapped_model, wrapped_dataset)

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

## 5. Automatically generate a test suite based on the scan results

If the automatic scan with `giskard.scan` found some issues with your model, you can automatically generate a set of
tests (a test suite) that will reproduce those issues.
You can then interactively debug the problems by uploading the generate test suite to Giskard UI.

```python
results = giskard.scan(wrapped_model, wrapped_dataset)

test_suite = results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

To debug the test suite in the Giskard UI, first make sure you have configured the Giskard server and started your local
worker ([see documentation here](../../guides/installation/index.md)).

Then, you can create a project and upload your test suite:

```python
from giskard import GiskardClient

url = "http://localhost:19000"
token = "my_API_Access_Token"
client = GiskardClient(url, token)
my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

test_suite.upload(client, "my_project")
```

Head over the to the UI (on http://localhost:19000 if you are running Giskard from a local Docker container) and you
will find your new test suite ready to be debugged.

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
