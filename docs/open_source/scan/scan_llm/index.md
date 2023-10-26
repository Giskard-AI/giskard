# 📚 LLM scan

The Giskard python library provides an automatic scan functionality designed to automatically detect [potential vulnerabilities](../../getting-started/key_vulnerabilities/performance_bias/index.md) affecting your ML model. It enables you to proactively identify and address key issues to ensure the reliability, fairness, and robustness of your Machine Learning models.

[//]: # (TODO: adapt whole page to a LLM use-case &#40;all code snippets&#41;)
## Step 1: Wrap your dataset

To scan your model, start by **wrapping your dataset**. This should be a validation or test set in Pandas format, as shown here:

```python
    # Wrap your Pandas DataFrame with Giskard.Dataset (validation or test set)
    giskard_dataset = giskard.Dataset(
        df=df,  # A pandas.DataFrame containing raw data (before pre-processing) and including ground truth variable.
        target="Survived",  # Ground truth variable
        name="Titanic dataset", # Optional: Give a name to your dataset
        cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]  # List of categorical columns. Optional, but improves quality of results if available.
    )
```

For further examples, check out the [tutorials section]().

[//]: # (TODO: check if we can put the following under a toggle:)
* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `df`: A `pandas.DataFrame` containing raw data (before pre-processing) and including ground truth variable. Extra columns not included as features of the model can remain in `df`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `target`: The column name in `df` corresponding to the ground truth variable.
    * `name`: Give a name to your dataset.
    * `cat_columns`: List of strings representing names of categorical columns.Can be binary,
      numerical, or textual with a few unique values. If not provided, column types will be inferred automatically.
    * `column_types`: Dictionary of column names and their types (numeric, category or text) for all columns of `df`.
      If not provided, column types will be inferred automatically.

## Step 2: Wrap your model

Next, **wrap your model**. You can wrap either the prediction function (recommended) or model object, as shown here:

:::::::{tab-set}
::::::{tab-item} Wrap a prediction function

Wrapping your model through the prediction function is the preferred method. The prediction function is any Python function that takes as input a <b>raw</b> Pandas dataframe, pre-processes your data and returns the predictions.

<b>Some important conditions:</b>

1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

:::::{tab-set}
::::{tab-item} Classification

```python
def prediction_function(df):
    preprocessed_df = demo_data_processing_function(df) # The pre-processor can be a pipeline of one-hot encoding, imputer, scaler, etc.
    return demo_classification_model.predict_proba(preprocessed_df)

wrapped_model = giskard.Model(
    model=prediction_function,
    model_type="classification",
    classification_labels=demo_classification_model.classes_,  # The order MUST be identical to the prediction_function's output order
    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'],  # Default: all columns of your dataset
    name="titanic_model", # Optional: give it a name to identify it in metadata
    # classification_threshold=0.5, # Optional: Default: 0.5
)
```

[//]: # (TODO: check if we can put the following under a toggle:)
* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns an array ($n\times m$) of
      probabilities corresponding to $n$ data entries (rows of `pandas.DataFrame`) and $m$ `classification_labels`. In the case of binary classification, an array ($n\times 1$) of probabilities is also accepted.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.
    * `classification_labels`: The list of unique categories for your dataset's target variable.
      If `classification_labels` is a list of $m$ elements, make sure that: `prediction_function` is returning a ($n\times m$) array of probabilities and `classification_labels` have the same order as the output of `prediction_function`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the column names of your feature. By default, `feature_names` are all the columns in your
      dataset. Make sure these features are all present and in the same order as they are in your training dataset.
    * `classification_threshold`: Model threshold for binary classification problems.

For further examples, check out the [tutorials section]().

::::
::::{tab-item} Regression

```python
import numpy as np

def prediction_function(df):
    preprocessed_df = demo_data_processing_function(df) # The pre-processor can be a pipeline of one-hot encoding, imputer, scaler, etc.
    return np.squeeze(demo_regression_model.predict(preprocessed_df))

wrapped_model = giskard.Model(
    model=prediction_function,
    model_type="regression",
    feature_names=['x'],  # Default: all columns of your dataset
    name="linear_model", # Optional: give it a name to identify it in metadata
)
```

[//]: # (TODO: check if we can put the following under a toggle:)
* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes `pandas.DataFrame` as input and returns an array $n$ of predictions
      corresponding to $n$ data entries (rows of `pandas.DataFrame`).
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the column names of your feature. By default, `feature_names` are all the columns in your
      dataset. Make sure these features are all present and in the same order as they are in your training dataset.

For further examples, check out the [tutorials section]().

::::
:::::
::::::
::::::{tab-item} Wrap a model object
Wrapping a model object allows Giskard to automatically infer the ML library of your `model`
object and provide a suitable serialization method (provided by `save_model` and `load_model` methods).

<b>Some important conditions:</b>

1. There will be an override of the `model_predict` method which should take as input the <b>raw</b> pandas dataframe
  and return the <b>probabilities</b> for each classification labels (classification) or predictions (regression or text_generation). 
2. The pre-defined serialization and prediction methods cover the `sklearn`, `catboost`, `pytorch`,
  `tensorflow`, `huggingface` and `langchain` libraries. If none of these libraries are detected, `cloudpickle`
  is used as the default for serialization. If this fails, we will ask you to also override the `save_model` and `load_model`
  methods where you provide your own serialization of the `model` object.

:::::{tab-set}
::::{tab-item} Classification

```python
class MyCustomModel(giskard.Model):
    def model_predict(self, df):
        preprocessed_df = demo_data_processing_function(df)
        return self.model.predict_proba(preprocessed_df)

wrapped_model = MyCustomModel(
    model=demo_classification_model,
    model_type="classification",
    classification_labels=demo_classification_model.classes_,  # Their order MUST be identical to the prediction_function's output order
    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked', 'Survived'],  # Default: all columns of your dataset
    name="titanic_model", # Optional: give it a name to identify it in metadata
    # classification_threshold=0.5, # Optional: Default: 0.5
    # model_postprocessing_function=None, # Optional
    # **kwargs # Additional model-specific arguments
)
```

[//]: # (TODO: check if we can put the following under a toggle:)
* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: Any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` (check
      the [tutorials](../../../tutorials/index.md)). If none of these libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we ask you to provide us with your own serialization method.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.
    * `classification_labels`: The list of unique categories for your dataset's target variable. If `classification_labels`
      is a list of $m$ elements, make sure that `prediction_function` is returning a ($n\times m$) array of probabilities and `classification_labels` have the same order as the output of the prediction function.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the column names of your feature. By default, `feature_names` are all the columns in your
      dataset.
    * `classification_threshold`: Model threshold for binary classification problems.
    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and
      returns any object that could be directly fed to `model`.
    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns
      an object of the same type and shape as the `model` output.
    * `**kwargs`: Additional model-specific arguments (See [Models](../../../reference/models/index.rst)).

For further examples, check out the [tutorials section]().

::::
::::{tab-item} Regression

```python
import numpy as np

class MyCustomModel(giskard.Model):
    def model_predict(self, df):
        preprocessed_df = demo_data_processing_function(df)
        return np.squeeze(self.model.predict(preprocessed_df))

wrapped_model = MyCustomModel(
    model=demo_regression_model,
    model_type="regression",
    feature_names=['x'],  # Default: all columns of your dataset
    name="my_regression_model", # Optional: give it a name to identify it in metadata
    # model_postprocessing_function=None, # Optional
    # **kwargs # Additional model-specific arguments
)
```

[//]: # (TODO: check if we can put the following under a toggle:)
* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: Any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` (check
      the [tutorials](../../../tutorials/index.md)). If none of these libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we
      ask you to provide us with your own serialization method.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset. Make sure these features are all present and in the same order as they are in your training dataset.
    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and
      returns any object that could be directly fed to `model`.
    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns
      an object of the same type and shape as the `model` output.
    * `**kwargs`: Additional model-specific arguments (See [Models](../../../reference/models/index.rst)).

For further examples, check out the [tutorials section]().

::::
:::::
::::::
:::::::

[//]: # (TODO: UPDATED VERSION OF CODE SNIPPETS ARE HERE)

[//]: # (:::::::{tab-set})

[//]: # (::::::{tab-item} Wrap a prediction function)

[//]: # (:::::{tab-set})

[//]: # (::::{tab-item} Classification)

[//]: # (Prediction function is any Python function that takes  input as <b>raw</b> pandas dataframe and returns the <b>probabilities</b> for each classification label.)

[//]: # ()
[//]: # (<b><u>Make sure that:</b></u>)

[//]: # ()
[//]: # (1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> &#40;categorical encoding, numerical scaling,)

[//]: # (   etc.&#41;.)

[//]: # (2. `prediction_function&#40;df[feature_names]&#41;` <b>does not return an error message</b>.)

[//]: # ()
[//]: # (```python)

[//]: # (from giskard import demo, Model)

[//]: # ()
[//]: # (demo_data_processing_function, demo_sklearn_model = demo.titanic_pipeline&#40;&#41;)

[//]: # ()
[//]: # (def prediction_function&#40;df&#41;:)

[//]: # (    # The pre-processor can be a pipeline of one-hot encoding, imputer, scaler, etc.)

[//]: # (    preprocessed_df = demo_data_processing_function&#40;df&#41;)

[//]: # (    return demo_sklearn_model.predict_proba&#40;preprocessed_df&#41;)

[//]: # ()
[//]: # (wrapped_model = Model&#40;)

[//]: # (    model=prediction_function,)

[//]: # (    model_type="classification",)

[//]: # (    classification_labels=demo_sklearn_model.classes_,  # Their order MUST be identical to the prediction_function's output order)

[//]: # (    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'],  # Default: all columns of your dataset)

[//]: # (    # name="titanic_model", # Optional)

[//]: # (    # classification_threshold=0.5, # Default: 0.5)

[//]: # (&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns an array &#40;$n\times m$&#41; of)

[//]: # (      probabilities corresponding)

[//]: # (      to $n$ data entries &#40;rows of `pandas.DataFrame`&#41; and $m$ `classification_labels`. In the case of binary)

[//]: # (      classification, an array  )

[//]: # (      &#40;$n\times 1$&#41; of probabilities is also accepted.)

[//]: # (    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.)

[//]: # (    * `classification_labels`: The list of unique categories contained in your dataset target variable.)

[//]: # (      If `classification_labels`)

[//]: # (      is a list of $m$ elements, make sure that:)

[//]: # (        * `prediction_function` is returning a &#40;$n\times m$&#41; array of probabilities.)

[//]: # (        * `classification_labels` have the same order as the output of `prediction_function`.)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as they are in your training dataset.)

[//]: # (    * `classification_threshold`: Model threshold for binary classification problems.)

[//]: # ()
[//]: # (::::)

[//]: # (::::{tab-item} Regression)

[//]: # (Prediction function is any Python function that takes the input as <b>raw</b> pandas dataframe and returns the <b>predictions</b> for your regression task.)

[//]: # ()
[//]: # (<b><u>Make sure that:</b></u>)

[//]: # ()
[//]: # (1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> &#40;categorical encoding, numerical scaling,)

[//]: # (   etc.&#41;.)

[//]: # (2. `prediction_function&#40;df[feature_names]&#41;` <b>does not return an error message</b>.)

[//]: # ()
[//]: # (```python)

[//]: # (import numpy as np)

[//]: # (from giskard import demo, Model)

[//]: # ()
[//]: # (demo_data_processing_function, reg = demo.linear_pipeline&#40;&#41;)

[//]: # ()
[//]: # (def prediction_function&#40;df&#41;:)

[//]: # (    preprocessed_df = demo_data_processing_function&#40;df&#41;)

[//]: # (    return np.squeeze&#40;reg.predict&#40;preprocessed_df&#41;&#41;)

[//]: # ()
[//]: # (wrapped_model = Model&#40;)

[//]: # (    model=prediction_function,)

[//]: # (    model_type="regression",)

[//]: # (    feature_names=['x'],  # Default: all columns of your dataset)

[//]: # (    # name="linear_model", # Optional)

[//]: # (&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: A prediction function that takes `pandas.DataFrame` as input and returns an array $n$ of predictions)

[//]: # (      corresponding)

[//]: # (      to $n$ data entries &#40;rows of `pandas.DataFrame`&#41;.)

[//]: # (    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as they are in your training dataset.)

[//]: # ()
[//]: # (::::)

[//]: # (::::{tab-item} Text generation)

[//]: # (Prediction function is any Python function that takes the input as <b>raw</b> pandas dataframe and returns the <b>predictions</b> for your text generation task.)

[//]: # ()
[//]: # (<b><u>Make sure that:</b></u>)

[//]: # ()
[//]: # (1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> &#40;categorical encoding, numerical scaling,)

[//]: # (   etc.&#41;.)

[//]: # (2. `prediction_function&#40;df[feature_names]&#41;` <b>does not return an error message</b>.)

[//]: # ()
[//]: # (```python)

[//]: # (import openai)

[//]: # (import giskard)

[//]: # (import pandas as pd)

[//]: # ()
[//]: # ()
[//]: # (# Define your text generation function)

[//]: # (def text_summarizer&#40;content: str&#41; -> str:)

[//]: # (    return openai.ChatCompletion.create&#40;)

[//]: # (        model="gpt-3.5-turbo",)

[//]: # (        messages=[)

[//]: # (            {"role": "system",)

[//]: # (             "content": "Summarize the text below as a bullet point list of the most important points."},)

[//]: # (            {"role": "user", "content": content})

[//]: # (        ])

[//]: # (    &#41;.choices[0].message.content)

[//]: # ()
[//]: # ()
[//]: # (# Wrap your function so that it takes a pandas DataFrame as an input and return a Series of generated text)

[//]: # (def prediction_function&#40;df: pd.DataFrame&#41; -> pd.Series:)

[//]: # (    return df['content'].map&#40;text_summarizer&#41;)

[//]: # ()
[//]: # ()
[//]: # (# Wrap your prediction_function into giskard)

[//]: # (# The model name and description MUST be explicit enough for the scan feature to work efficiently)

[//]: # (model = giskard.Model&#40;prediction_function, model_type='text_generation',)

[//]: # (                      name="Text summarizer",)

[//]: # (                      description="Summarize text by giving a bullet point list of the most important points found in the text",)

[//]: # (                      feature_names=['content']&#41;)

[//]: # (```)

[//]: # ()
[//]: # (```python)

[//]: # (from langchain.chains import LLMChain)

[//]: # (from langchain.llms.fake import FakeListLLM)

[//]: # (from langchain.prompts import PromptTemplate)

[//]: # (from giskard import Model)

[//]: # ()
[//]: # (responses = [)

[//]: # (    "\n\nHueFoots.", "\n\nEcoDrive Motors.", )

[//]: # (    "\n\nRainbow Socks.", "\n\nNoOil Motors."])

[//]: # ()
[//]: # (llm = FakeListLLM&#40;responses=responses&#41;)

[//]: # (prompt = PromptTemplate&#40;)

[//]: # (    input_variables=["product"],)

[//]: # (    template="What is a good name for a company that makes {product}?",)

[//]: # (&#41;)

[//]: # (chain = LLMChain&#40;llm=llm, prompt=prompt&#41;)

[//]: # ()
[//]: # (def prediction_function&#40;df&#41;:)

[//]: # (    return [chain.predict&#40;**data&#41; for data in df.to_dict&#40;'records'&#41;])

[//]: # ()
[//]: # (wrapped_model = Model&#40;prediction_function, model_type='text_generation'&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: A prediction function that takes `pandas.DataFrame` as input and returns an array $n$ of predictions)

[//]: # (      corresponding)

[//]: # (      to $n$ data entries &#40;rows of `pandas.DataFrame`&#41;.)

[//]: # (    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as they are in your training dataset.)

[//]: # ()
[//]: # (::::)

[//]: # (:::::)

[//]: # (::::::)

[//]: # (::::::{tab-item} Wrap a model object)

[//]: # (Providing the model object to `Model` allows us to automatically infer the ML library of your `model`)

[//]: # (object and provide a suitable serialization method &#40;provided by `save_model` and `load_model` methods&#41;.)

[//]: # ()
[//]: # (This requires:)

[//]: # ()
[//]: # (- <b><u>Mandatory</u></b>: Overriding the `model_predict` method which should take the input as <b>raw</b> pandas dataframe)

[//]: # (  and return the <b>probabilities</b> for each classification labels &#40;classification&#41; or predictions &#40;regression or text_generation&#41;.)

[//]: # (- <b><u>Optional</u></b>: Our pre-defined serialization and prediction methods cover the `sklearn`, `catboost`, `pytorch`,)

[//]: # (  `tensorflow`, `huggingface` and `langchain` libraries. If none of these libraries are detected, `cloudpickle`)

[//]: # (  is used as the default for serialization. If this fails, we will ask you to also override the `save_model` and `load_model`)

[//]: # (  methods where you provide your own serialization of the `model` object.)

[//]: # ()
[//]: # (:::::{tab-set})

[//]: # (::::{tab-item} Classification)

[//]: # ()
[//]: # (```python)

[//]: # (from giskard import demo, Model)

[//]: # ()
[//]: # (demo_data_processing_function, demo_sklearn_model = demo.titanic_pipeline&#40;&#41;)

[//]: # ()
[//]: # (class MyCustomModel&#40;Model&#41;:)

[//]: # (    def model_predict&#40;self, df&#41;:)

[//]: # (        preprocessed_df = demo_data_processing_function&#40;df&#41;)

[//]: # (        return self.model.predict_proba&#40;preprocessed_df&#41;)

[//]: # ()
[//]: # (wrapped_model = MyCustomModel&#40;)

[//]: # (    model=demo_sklearn_model,)

[//]: # (    model_type="classification",)

[//]: # (    classification_labels=demo_sklearn_model.classes_,  # Their order MUST be identical to the prediction_function's output order)

[//]: # (    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare',)

[//]: # (                 'Embarked', 'Survived'],  # Default: all columns of your dataset)

[//]: # (    # name="titanic_model", # Optional)

[//]: # (    # classification_threshold=0.5, # Default: 0.5)

[//]: # (    # model_postprocessing_function=None, # Optional)

[//]: # (    # **kwargs # Additional model-specific arguments)

[//]: # (&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` &#40;check)

[//]: # (      the [tutorials]&#40;../../tutorials/index.md&#41;&#41;. If none of these)

[//]: # (      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we)

[//]: # (      ask you to provide us with your own serialization method.)

[//]: # (    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.)

[//]: # (    * `classification_labels`: The list of unique categories contained in your dataset target variable.)

[//]: # (      If `classification_labels`)

[//]: # (      is a list of $m$ elements, make sure that:)

[//]: # (        * `prediction_function` is returning a &#40;$n\times m$&#41; array of probabilities.)

[//]: # (        * `classification_labels` have the same order as the output of `prediction_function`.)

[//]: # ()
[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as they are in your training dataset.)

[//]: # (    * `classification_threshold`: Model threshold for binary classification problems.)

[//]: # (    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and)

[//]: # (      returns any object that could be directly fed to `model`.)

[//]: # (    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns)

[//]: # (      an object of the same type and shape as the `model` output.)

[//]: # (    * `**kwargs`: Additional model-specific arguments &#40;See [Models]&#40;../../reference/models/index.rst&#41;&#41;.)

[//]: # ()
[//]: # (::::)

[//]: # (::::{tab-item} Regression)

[//]: # ()
[//]: # (```python)

[//]: # (import numpy as np)

[//]: # (from giskard import demo, Model)

[//]: # ()
[//]: # (demo_data_processing_function, reg = demo.linear_pipeline&#40;&#41;)

[//]: # ()
[//]: # (class MyCustomModel&#40;Model&#41;:)

[//]: # (    def model_predict&#40;self, df&#41;:)

[//]: # (        preprocessed_df = demo_data_processing_function&#40;df&#41;)

[//]: # (        return np.squeeze&#40;self.model.predict&#40;preprocessed_df&#41;&#41;)

[//]: # ()
[//]: # (wrapped_model = MyCustomModel&#40;)

[//]: # (    model=reg,)

[//]: # (    model_type="regression",)

[//]: # (    feature_names=['x'],  # Default: all columns of your dataset)

[//]: # (    # name="my_regression_model", # Optional)

[//]: # (    # model_postprocessing_function=None, # Optional)

[//]: # (    # **kwargs # Additional model-specific arguments)

[//]: # (&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` &#40;check)

[//]: # (      the [tutorials]&#40;../../tutorials/index.md&#41;&#41;. If none of these)

[//]: # (      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we)

[//]: # (      ask you to provide us with your own serialization method.)

[//]: # (    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as your training dataset.)

[//]: # (    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and)

[//]: # (      returns any object that could be directly fed to `model`.)

[//]: # (    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns)

[//]: # (      an object of the same type and shape as the `model` output.)

[//]: # (    * `**kwargs`: Additional model-specific arguments &#40;See [Models]&#40;../../reference/models/index.rst&#41;&#41;.)

[//]: # ()
[//]: # (::::)

[//]: # (::::{tab-item} Text generation)

[//]: # ()
[//]: # (```python)

[//]: # (from langchain.chains import LLMChain)

[//]: # (from langchain.llms.fake import FakeListLLM)

[//]: # (from langchain.prompts import PromptTemplate)

[//]: # (import giskard)

[//]: # ()
[//]: # (responses = [)

[//]: # (    "\n\nHueFoots.", "\n\nEcoDrive Motors.", )

[//]: # (    "\n\nRainbow Socks.", "\n\nNoOil Motors."])

[//]: # ()
[//]: # (llm = FakeListLLM&#40;responses=responses&#41;)

[//]: # (prompt = PromptTemplate&#40;)

[//]: # (    input_variables=["product"],)

[//]: # (    template="What is a good name for a company that makes {product}?",)

[//]: # (&#41;)

[//]: # (chain = LLMChain&#40;llm=llm, prompt=prompt&#41;)

[//]: # ()
[//]: # (wrapped_model = giskard.Model&#40;chain, model_type='text_generation'&#41;)

[//]: # (```)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Mandatory parameters`**</mark>)

[//]: # (    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` &#40;check)

[//]: # (      the [tutorials]&#40;../../tutorials/index.md&#41;&#41;. If none of these)

[//]: # (      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we)

[//]: # (      ask you to provide us with your own serialization method.)

[//]: # (    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.)

[//]: # ()
[//]: # (* <mark style="color:red;">**`Optional parameters`**</mark>)

[//]: # (    * `name`: Name of the wrapped model.)

[//]: # (    * `description`: An optional description of the model)

[//]: # (    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your)

[//]: # (      dataset.)

[//]: # (      Make sure these features are in the same order as your training dataset.)

[//]: # (    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and)

[//]: # (      returns any object that could be directly fed to `model`.)

[//]: # (    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns)

[//]: # (      an object of the same type and shape as the `model` output.)

[//]: # (    * `**kwargs`: Additional model-specific arguments &#40;See [Models]&#40;../../reference/models/index.rst&#41;&#41;.)

[//]: # ()
[//]: # (::::)

[//]: # (:::::)

[//]: # (::::::)

[//]: # (:::::::)

## Step 3: Scan you model

Now you can scan your model and display your scan report:

```python

    scan_results = giskard.scan(giskard_model, giskard_dataset)
    display(scan_results)  # in your notebook
```
../../assets/scan_widget.html

[//]: # (TODO: add scan html or png)

If you are not working in a notebook or want to save the results for later, you can save them to an HTML file like this:

```python

    scan_results.to_html("model_scan_results.html")
```

## What's next? 

Your scan results may have highlighted important vulnerabilities. There are 2 important actions you can take next:

### 1. Generate a test suite from your scan results to:

[//]: # (TODO: list other benefits of test suites)
* Turn the issues you found into actionable tests that you can directly integrate in your CI/CD pipeline

```python

    test_suite = scan_results.generate_test_suite("My first test suite")

    # You can run the test suite locally to verify that it reproduces the issues
    test_suite.run()
```

Jump to the [test customization]() and [test integration]() sections to find out everything you can do with test suites.

### 2. Upload your test suite to the Giskard Hub to:
* Debug your tests to diagnose the identified issues
* Compare the quality of different models to decide which one to promote
* Create more domain-specific tests relevant to your use case
* Share results, and collaborate with your team to integrate business feedback

[Here's a demo](HF link) of the Giskard Hub in action.

## Troubleshooting

If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.

