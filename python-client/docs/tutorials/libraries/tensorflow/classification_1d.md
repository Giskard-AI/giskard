# Sentiment analysis model

## Libraries import
```python
from pathlib import Path
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers
import tests.utils
from giskard import Model, Dataset
```

## Wrap dataset
```python
dataset = tf.keras.utils.get_file("aclImdb",
                                  "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz",
                                  untar=True)

raw_test_ds = tf.keras.utils.text_dataset_from_directory(
    Path(dataset) / 'test',
    batch_size=batch_size)

test_dataset = {'Review': [], 'Label': []}
for text_batch, label_batch in raw_test_ds.take(782):
    for i in range(8):
        test_dataset['Review'].append(text_batch.numpy()[i])
        test_dataset['Label'].append(label_batch.numpy()[i])
    test_df = pd.DataFrame.from_dict(test_dataset)
```
```python
wrapped_dataset = Dataset(test_df.head(), 
                               name="test dataset", 
                               target="Label")
```

## Wrap model
```python
batch_size = 32
max_features = 10000
sequence_length = 250
vectorize_layer = tf.keras.layers.TextVectorization(
    standardize='lower_and_strip_punctuation',
    max_tokens=max_features,
    output_mode='int',
    output_sequence_length=sequence_length)

batch_size = 32
seed = 42

raw_train_ds = tf.keras.utils.text_dataset_from_directory(
    Path(dataset) / 'train',
    batch_size=batch_size,
    validation_split=0.2,
    subset='training',
    seed=seed)

# Make a text-only dataset (without labels), then call adapt
train_text = raw_train_ds.map(lambda x, y: x)
vectorize_layer.adapt(train_text)

embedding_dim = 16

model = tf.keras.Sequential([
    layers.Embedding(max_features + 1, embedding_dim),
    layers.Dropout(0.2),
    layers.GlobalAveragePooling1D(),
    layers.Dropout(0.2),
    layers.Dense(1) # works also with the case of layers.Dense(2)
])

model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
              optimizer='adam',
              metrics=['accuracy'])

export_model = tf.keras.Sequential([
    vectorize_layer,
    model
])

export_model.compile(
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=['accuracy']
)

def FromPandastoTFModelInput(test_df):
    test_dataset = test_df.squeeze(axis=1)
    test_dataset = list(test_dataset)
    return test_dataset
```
```python
wrapped_model = Model(name="Tensorflow_text_classification",
                           model=export_model,
                           feature_names=['Review'],
                           model_type="classification",
                           classification_labels=[0, 1],
                           data_preprocessing_function=FromPandastoTFModelInput)
```