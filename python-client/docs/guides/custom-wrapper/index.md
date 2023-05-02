# ⚒️ Wrap any python function with Giskard
In this section, we explain additional ways that enable you to wrap any model you have in Giskard.


## From scratch
To create your own wrapper that doesn't necessarily rely on any of the ML libraries we support:
`sklearn`, `catboost`, `pytorch`, `tensorflow` and `huggingface`. You can extend our {class}`~giskard.CustomModel` wrapper
that relies on `cloudpickle` for serialisation as follows:
```python
from giskard import CustomModel
class my_custom_model(CustomModel):

    def _predict_df(self, some_df: pd.DataFrame):
        """
        Your code to extract predictions from some_df goes here
        """
        return predictions
```
Which you can easily then use in giskard as follows:
```python
my_wrapped_model = my_custom_model(name="my_wrapped_model",
                                   model_type="classification", 
                                   feature_names=["feature1", "feature2", "feature3"],
                                   classification_threshold = 0.8,
                                   classification_labels=["label1", "label2"])
```
This will also allow you to upload your model to the giskard user interface.

## From a URL
```python
from giskard import CustomModel
import requests
class my_url_based_model(CustomModel):

    def _predict_df(input_data: pd.DataFrame):
        # Set up the API endpoint URL and parameters
        api_endpoint = "https://api.example.com/predict"
        api_params = {
            "input": input_data
        }
    
        # Send a GET request to the API endpoint and get the response
        response = requests.get(api_endpoint, params=api_params)
    
        # Print response status code if an error has occurred
        print(response.raise_for_status())
    
        # Extract the predictions from the JSON response
        predictions = response.json()["predictions"]
    
        return predictions
```
Which you can easily then use in giskard as follows:
```python
my_wrapped_model = my_url_based_model(name="my_wrapped_model",
                                   model_type="classification", 
                                   feature_names=["feature1", "feature2", "feature3"],
                                   classification_threshold = 0.8,
                                   classification_labels=["label1", "label2"])
```
This will also allow you to upload your model to the giskard user interface.

## Based on Giskard wrappers
We currently have 5 pre-defined wrappers with their own methods of serializations that you can extend:

- {class}`~giskard.SKLearnModel`
- {class}`~giskard.CatboostModel`
- {class}`~giskard.PyTorchModel`
- {class}`~giskard.TensorFlowModel`
- {class}`~giskard.HuggingFaceModel`

Let's start from the following tutorial: <project:../../guides/tutorials/pytorch/sst2_iterable.md>. Where instead of
passing a `model`, `data_preprocessing_function` and `model_postprocessing_function` to `wrap_model` as follows:
```python
wrapped_model = wrap_model(name="SST2-XLMR_BASE_ENCODER",
                           model=model,
                           feature_names=["text"],
                           model_type="classification",
                           classification_labels=classification_labels,
                           data_preprocessing_function=pandas_to_torch,
                           model_postprocessing_function=my_softmax,
)
```
we decide to wrap the prediction pipeline in a `prediction_function`:
```python
def prediction_function(some_df: pd.DataFrame):
    preprocessed_data = pandas_to_torch(some_df)
    dataloader = DataLoader(preprocessed_data, batch_size=None)
    predictions = []
    with torch.no_grad():
        for batch in dataloader:
            input = F.to_tensor(batch["token_ids"], padding_value=padding_idx).to(DEVICE)
            output = model(input)
            prediction = softmax(output).detach().numpy()
            predictions.extend(prediction)

    return np.array(predictions)
```
In that case, we could feed this `prediction_function` to an extended `~giskard.PyTorchModel` as follow:
```python
from giskard import PyTorchModel
class my_PyTorchModel(PyTorchModel):
    should_save_model_class = True

    def predict_proba(self, some_df: pd.DataFrame):
        # ========= your prediction_function =========
        def prediction_function(some_df: pd.DataFrame):
            preprocessed_data = pandas_to_torch(some_df)
            dataloader = DataLoader(preprocessed_data, batch_size=None)
            predictions = []
            with torch.no_grad():
                for batch in dataloader:
                    input = F.to_tensor(batch["token_ids"], padding_value=padding_idx).to(DEVICE)
                    output = self.model(input) # <---- Important
                    prediction = softmax(output).detach().numpy()
                    predictions.extend(prediction)
        
            return np.array(predictions)
        # ============================================

        return prediction_function(some_df)
```
and finally we can use it as follows:
```python
wrapped_model = my_PyTorchModel(name="SST2-XLMR_BASE_ENCODER",
                               model=model,
                               feature_names=["text"],
                               model_type="classification",
                               classification_labels=classification_labels,
                               # data_preprocessing_function=pandas_to_torch, #<--- this is now inside prediction_function
                               # model_postprocessing_function=my_softmax, #<--- this is now inside prediction_function
                               )
```