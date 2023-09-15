# 🎁 Wrap your ML model

To scan, test and debug your model, you need to wrap it into a Giskard Model. Your model can use any ML library (`HuggingFace`, `PyTorch`, `Tensorflow`, `Sklearn`, etc.) and can be any Python function that respects the right signature. You can wrap your model in two different ways:

- <b> Wrap a prediction function</b> that contains all your data pre-processing steps.
- <b> Wrap a model object</b> in addition to a data pre-processing function.

:::{hint}
Choose <b>"Wrap a model object"</b> if your model is not serializable by `cloudpickle` (e.g. TensorFlow models).
:::

:::::::{tab-set}
::::::{tab-item} Wrap a prediction function
:::::{tab-set}
::::{tab-item} Classification
Prediction function is any Python function that takes  input as <b>raw</b> pandas dataframe and returns the <b>probabilities</b> for each classification label.

<b><u>Make sure that:</b></u>

1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

```python
from giskard import demo, Model

data_preprocessor, titanic_pretrained_model = demo.titanic_pipeline()

def prediction_function(df):
    # The pre-processor can be a pipeline of one-hot encoding, imputer, scaler, etc.
    preprocessed_df = data_preprocessor(df)
    return titanic_pretrained_model.predict_proba(preprocessed_df)

wrapped_model = Model(
    model=prediction_function,
    model_type="classification",
    classification_labels=titanic_pretrained_model.classes_,  # Their order MUST be identical to the prediction_function's output order
    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'],  # Default: all columns of your dataset
    # name="titanic_model", # Optional
    # classification_threshold=0.5, # Default: 0.5
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns an array ($n\times m$) of
      probabilities corresponding
      to $n$ data entries (rows of `pandas.DataFrame`) and $m$ `classification_labels`. In the case of binary
      classification, an array  
      ($n\times 1$) of probabilities is also accepted.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.
    * `classification_labels`: The list of unique categories contained in your dataset target variable.
      If `classification_labels`
      is a list of $m$ elements, make sure that:
        * `prediction_function` is returning a ($n\times m$) array of probabilities.
        * `classification_labels` have the same order as the output of `prediction_function`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as they are in your training dataset.
    * `classification_threshold`: Model threshold for binary classification problems.

::::
::::{tab-item} Regression
Prediction function is any Python function that takes the input as <b>raw</b> pandas dataframe and returns the <b>predictions</b> for your regression task.

<b><u>Make sure that:</b></u>

1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

```python
import numpy as np
from giskard import demo, Model

data_preprocessor, reg = demo.linear_pipeline()

def prediction_function(df):
    preprocessed_df = data_preprocessor(df)
    return np.squeeze(reg.predict(preprocessed_df))

wrapped_model = Model(
    model=prediction_function,
    model_type="regression",
    feature_names=['x'],  # Default: all columns of your dataset
    # name="linear_model", # Optional
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes `pandas.DataFrame` as input and returns an array $n$ of predictions
      corresponding
      to $n$ data entries (rows of `pandas.DataFrame`).
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as they are in your training dataset.

::::
::::{tab-item} Text generation
Prediction function is any Python function that takes the input as <b>raw</b> pandas dataframe and returns the <b>predictions</b> for your text generation task.

<b><u>Make sure that:</b></u>

1. `prediction_function` encapsulates all the <b>data pre-processing steps</b> (categorical encoding, numerical scaling,
   etc.).
2. `prediction_function(df[feature_names])` <b>does not return an error message</b>.

```python
import openai
import giskard
import pandas as pd


# Define your text generation function
def text_summarizer(content: str) -> str:
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "Summarize the text below as a bullet point list of the most important points."},
            {"role": "user", "content": content}
        ]
    ).choices[0].message.content


# Wrap your function so that it takes a pandas DataFrame as an input and return a Series of generated text
def prediction_function(df: pd.DataFrame) -> pd.Series:
    return df['content'].map(text_summarizer)


# Wrap your prediction_function into giskard
# The model name and description MUST be explicit enough for the scan feature to work efficiently
model = giskard.Model(prediction_function, model_type='text_generation',
                      name="Text summarizer",
                      description="Summarize text by giving a bullet point list of the most important points found in the text",
                      feature_names=['content'])
```

```python
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM
from langchain.prompts import PromptTemplate
from giskard import Model

responses = [
    "\n\nHueFoots.", "\n\nEcoDrive Motors.", 
    "\n\nRainbow Socks.", "\n\nNoOil Motors."]

llm = FakeListLLM(responses=responses)
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}?",
)
chain = LLMChain(llm=llm, prompt=prompt)

def prediction_function(df):
    return [chain.predict(**data) for data in df.to_dict('records')]

wrapped_model = Model(prediction_function, model_type='text_generation')
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes `pandas.DataFrame` as input and returns an array $n$ of predictions
      corresponding
      to $n$ data entries (rows of `pandas.DataFrame`).
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as they are in your training dataset.

::::
:::::
::::::
::::::{tab-item} Wrap a model object
Providing the model object to `Model` allows us to automatically infer the ML library of your `model`
object and provide a suitable serialization method (provided by `save_model` and `load_model` methods).

This requires:

- <b><u>Mandatory</u></b>: Overriding the `model_predict` method which should take the input as <b>raw</b> pandas dataframe
  and return the <b>probabilities</b> for each classification labels (classification) or predictions (regression or text_generation).
- <b><u>Optional</u></b>: Our pre-defined serialization and prediction methods cover the `sklearn`, `catboost`, `pytorch`,
  `tensorflow`, `huggingface` and `langchain` libraries. If none of these libraries are detected, `cloudpickle`
  is used as the default for serialization. If this fails, we will ask you to also override the `save_model` and `load_model`
  methods where you provide your own serialization of the `model` object.

:::::{tab-set}
::::{tab-item} Classification

```python
from giskard import demo, Model

data_preprocessor, titanic_pretrained_model = demo.titanic_pipeline()

class MyCustomModel(Model):
    def model_predict(self, df):
        preprocessed_df = data_preprocessor(df)
        return self.model.predict_proba(preprocessed_df)

wrapped_model = MyCustomModel(
    model=titanic_pretrained_model,
    model_type="classification",
    classification_labels=titanic_pretrained_model.classes_,  # Their order MUST be identical to the prediction_function's output order
    feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare',
                 'Embarked', 'Survived'],  # Default: all columns of your dataset
    # name="titanic_model", # Optional
    # classification_threshold=0.5, # Default: 0.5
    # model_postprocessing_function=None, # Optional
    # **kwargs # Additional model-specific arguments
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` (check
      the [tutorials](../../tutorials/index.md)). If none of these
      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we
      ask you to provide us with your own serialization method.
    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.
    * `classification_labels`: The list of unique categories contained in your dataset target variable.
      If `classification_labels`
      is a list of $m$ elements, make sure that:
        * `prediction_function` is returning a ($n\times m$) array of probabilities.
        * `classification_labels` have the same order as the output of `prediction_function`.


* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as they are in your training dataset.
    * `classification_threshold`: Model threshold for binary classification problems.
    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and
      returns any object that could be directly fed to `model`.
    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns
      an object of the same type and shape as the `model` output.
    * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::
::::{tab-item} Regression

```python
import numpy as np
from giskard import demo, Model

data_preprocessor, reg = demo.linear_pipeline()

class MyCustomModel(Model):
    def model_predict(self, df):
        preprocessed_df = data_preprocessor(df)
        return np.squeeze(self.model.predict(preprocessed_df))

wrapped_model = MyCustomModel(
    model=reg,
    model_type="regression",
    feature_names=['x'],  # Default: all columns of your dataset
    # name="my_regression_model", # Optional
    # model_postprocessing_function=None, # Optional
    # **kwargs # Additional model-specific arguments
)
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` (check
      the [tutorials](../../tutorials/index.md)). If none of these
      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we
      ask you to provide us with your own serialization method.
    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as your training dataset.
    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and
      returns any object that could be directly fed to `model`.
    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns
      an object of the same type and shape as the `model` output.
    * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::
::::{tab-item} Text generation

```python
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM
from langchain.prompts import PromptTemplate
import giskard

responses = [
    "\n\nHueFoots.", "\n\nEcoDrive Motors.", 
    "\n\nRainbow Socks.", "\n\nNoOil Motors."]

llm = FakeListLLM(responses=responses)
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}?",
)
chain = LLMChain(llm=llm, prompt=prompt)

wrapped_model = giskard.Model(chain, model_type='text_generation')
```

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: Could be any model from `sklearn`, `catboost`, `pytorch`, `tensorflow`, `huggingface` or `langchain` (check
      the [tutorials](../../tutorials/index.md)). If none of these
      libraries apply to you, we try to serialize your model with `cloudpickle`. If that also does not work, we
      ask you to provide us with your own serialization method.
    * `model_type`: The type of the model, either `regression`, `classification` or `text_generation`.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Name of the wrapped model.
    * `description`: An optional description of the model
    * `feature_names`: An optional list of the feature names. By default, `feature_names` are all the columns in your
      dataset.
      Make sure these features are in the same order as your training dataset.
    * `data_preprocessing_function`: A function that takes a `pandas.DataFrame` as raw input, applies pre-processing and
      returns any object that could be directly fed to `model`.
    * `model_postprocessing_function`: A function that takes a `model` output as input, applies post-processing and returns
      an object of the same type and shape as the `model` output.
    * `**kwargs`: Additional model-specific arguments (See [Models](../../reference/models/index.rst)).

::::
:::::
::::::
:::::::

### Model-specific [tutorials](../../tutorials/index.md)

To check some **examples** of model wrapping, have a look at our tutorial section. We present there some **notebooks** based on:
* [**ML libraries**](../../tutorials/libraries/index.md): HuggingFace, Langchain, API REST, PyTorch, Scikit-learn, LightGBM, Tensorflow
* [**ML task**](../../tutorials/tasks/index.md): Classification, Regression and Text generation
* [**Data types**](../../tutorials/data-types/index.md): Tabular, Text and Text generataion

## Upload your model to the Giskard server

Uploading the model to the Giskard server enables you to:
* Compare your model with others using a test suite.
* Gather feedback from your colleagues regarding your model.
* Debug your model effectively in case of test failures.
* Develop new tests that incorporate additional domain knowledge.

To upload your model to the Giskard server, go to [Upload an object to the Giskard server](../upload/index.md).
:::
