"""
To scan, test and debug your model, you need to wrap it into a Giskard Model.
Your model can use any ML library (``sklearn``, ``catboost``, ``pytorch``, ``tensorflow``,
``huggingface`` and ``langchain``) and can be any Python function that respects the right signature.

You can wrap your model in two different ways:

1. Wrap a prediction function that contains all your data pre-processing steps.
   Prediction function is any Python function that takes input as raw pandas dataframe and returns the probabilities
   for each classification labels (classification) or predictions (regression or text_generation).

   Make sure that:

   - ``prediction_function`` encapsulates all the data pre-processing steps (categorical encoding, numerical scaling, etc.).
   - ``prediction_function(df[feature_names])`` does not return an error message.
2. Wrap a model object in addition to a data pre-processing function.
   Providing the model object to Model allows us to automatically infer the ML library of your model object and
   provide a suitable serialization method (provided by ``save_model`` and ``load_model`` methods).

   This requires:

   - Mandatory: Overriding the model_predict method which should take the input as raw pandas dataframe and return
   the probabilities for each classification labels (classification) or predictions (regression or text_generation).
   - Optional: Our pre-defined serialization and prediction methods cover the ``sklearn``, ``catboost``, ``pytorch``,
   ``tensorflow``, ``huggingface`` and ``langchain`` libraries.
   If none of these libraries are detected, cloudpickle is used as the default for serialization.
   If this fails, we will ask you to also override the ``save_model`` and ``load_model`` methods where you provide your own
   serialization of the model object.
"""

from .automodel import Model

__all__ = ["Model"]
