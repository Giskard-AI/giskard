# 🔬 Wrap your ML model

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
  model=prediction_function,
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
  model=prediction_function,
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
    the [tutorials](docs/tutorials/index.md)). If none of these
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
  * `**kwargs`: Additional model-specific arguments (See [Models](docs/reference/models/index.rst)).

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
    the [tutorials](docs/tutorials/index.md)). If none of these
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
  * `**kwargs`: Additional model-specific arguments (See [Models](docs/reference/models/index.rst)).

::::
:::::
::::::
:::::::

### Model-specific [tutorials](docs/tutorials/index.md)

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
