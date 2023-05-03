# `AutoModelForSequenceClassification` pipeline

## Libraries import
```python
# For the complete tutorial, check: https://huggingface.co/docs/transformers/tasks/sequence_classification
import pandas as pd
from transformers import pipeline
from giskard import wrap_model, wrap_dataset
```
## Wrap dataset
```python
text = "This was a masterpiece. Not completely faithful to the books, but enthralling from beginning to end. Might be my favorite of the three."

raw_data = {
    "text": text,
    "label": "POSITIVE",
}
test_df = pd.DataFrame(raw_data, columns=["text", "label"], index=[0])
```
```python
wrapped_dataset = wrap_dataset(test_df, 
                               name="test dataset", 
                               target="label")
```
## Wrap model
```python
my_classifier = pipeline(task="sentiment-analysis", model="stevhliu/my_awesome_model")

# The labels do not seem to correctly configured for "stevhliu/my_awesome_model" so we're using here the default
# labels provided by pipeline
label2id = {"LABEL_0": 0, "LABEL_1": 1}

feature_names = ["text"]

def my_preproccessing_function(df):
    return df["text"].values

```
```python
wrapped_model = wrap_model(
    name="stevhliu/my_awesome_model",
    model=my_classifier,
    feature_names=feature_names,
    model_type="classification",
    classification_labels=list(label2id.keys()),
    data_preprocessing_function=my_preproccessing_function,
)
```