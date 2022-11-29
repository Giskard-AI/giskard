import httpretty
gsk_url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "multipart/form-data; boundary="
model_name = "uploaded model"
b_content_type = b"application/json"

"""
problem seen in https://github.com/Giskard-AI/giskard-examples/blob/main/Text_classification_Using_Tensorflow_Neural_Network.ipynb
with tensorflow==2.11.0
"""

import os
import shutil
import tensorflow as tf
import pandas as pd
from tensorflow.keras import layers
import pytest

## initiate Giskard project
from giskard.client.giskard_client import GiskardClient
from giskard.client.project import GiskardProject

#@pytest.mark.skip(reason="GSK-382 BadZipFile upon inspect of tensorflow model with python3.10")
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_upload_tensorflow():
    print("tensorflow version: ", tf.__version__)

    httpretty.register_uri(httpretty.POST, "http://giskard-host:12345/api/v2/project/models/upload")

    client = GiskardClient(gsk_url, token)
    project = GiskardProject(client.session, "test-project", 1)

    max_features = 10000
    sequence_length = 250
    embedding_dim = 16

    model = tf.keras.Sequential([
        layers.Embedding(max_features + 1, embedding_dim),
        layers.Dropout(0.2),
        layers.GlobalAveragePooling1D(),
        layers.Dropout(0.2),
        layers.Dense(2),
        tf.keras.layers.Softmax()
    ])

    def vectorize_text(text, label):
        text = tf.expand_dims(text, -1)
        return vectorize_layer(text), label

    data_url = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"

    dataset = tf.keras.utils.get_file("aclImdb_v1", data_url,
                                      untar=True, cache_dir='.',
                                      cache_subdir='')

    dataset_dir = os.path.join(os.path.dirname(dataset), 'aclImdb')
    train_dir = os.path.join(dataset_dir, 'train')
    sample_file = os.path.join(train_dir, 'pos/1181_9.txt')
    remove_dir = os.path.join(train_dir, 'unsup')
    shutil.rmtree(remove_dir)
    batch_size = 32
    seed = 42

    raw_train_ds = tf.keras.utils.text_dataset_from_directory(
        'aclImdb/train',
        batch_size=batch_size,
        validation_split=0.2,
        subset='training',
        seed=seed)
    raw_val_ds = tf.keras.utils.text_dataset_from_directory(
        'aclImdb/train',
        batch_size=batch_size,
        validation_split=0.2,
        subset='validation',
        seed=seed)
    raw_test_ds = tf.keras.utils.text_dataset_from_directory(
        'aclImdb/test',
        batch_size=batch_size)
    train_dataset = {'Review':[], 'Label':[]}
    for text_batch, label_batch in raw_train_ds.take(625):
        for i in range(32):
            train_dataset['Review'].append(text_batch.numpy()[i])
            train_dataset['Label'].append(label_batch.numpy()[i])

    train_df = pd.DataFrame.from_dict(train_dataset)
    val_dataset = {'Review':[], 'Label':[]}
    for text_batch, label_batch in raw_val_ds.take(157):
        for i in range(8):
            val_dataset['Review'].append(text_batch.numpy()[i])
            val_dataset['Label'].append(label_batch.numpy()[i])

    val_df = pd.DataFrame.from_dict(val_dataset)

    test_dataset = {'Review':[], 'Label':[]}
    for text_batch, label_batch in raw_test_ds.take(782):
        for i in range(8):
            test_dataset['Review'].append(text_batch.numpy()[i])
            test_dataset['Label'].append(label_batch.numpy()[i])
        test_df = pd.DataFrame.from_dict(test_dataset)

    # Make a text-only dataset (without labels), then call adapt
    train_text = raw_train_ds.map(lambda x, y: x)

    vectorize_layer = tf.keras.layers.TextVectorization(
        standardize='lower_and_strip_punctuation',
        max_tokens=max_features,
        output_mode='int',
        output_sequence_length=sequence_length)

    vectorize_layer.adapt(train_text)

    train_ds = raw_train_ds.map(vectorize_text)
    val_ds = raw_val_ds.map(vectorize_text)
    test_ds = raw_test_ds.map(vectorize_text)
    epochs = 1

    model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
                  optimizer='adam',
                  metrics=['accuracy'])
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs)

    export_model = tf.keras.Sequential([
        vectorize_layer,
        model
    ])

    export_model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=['accuracy']
    )

    def predict(test_dataset):
        test_dataset= test_dataset.squeeze(axis=1)
        test_dataset = list(test_dataset)
        predictions = export_model.predict(test_dataset)

        return predictions

    column_types = {'Review':"text",
                    'Label':"category"}

    examples = [
        "The movie was great!",
        "The movie was okay.",
        "The movie was terrible..."
    ]

    print(export_model.predict(examples))

    project.upload_model(
        prediction_function=predict, # Python function which takes pandas dataframe as input and returns probabilities for classification model OR returns predictions for regression model
        model_type='classification', # "classification" for classification model OR "regression" for regression model
        feature_names=['Review'], # List of the feature names of prediction_function
        name="Tensorflow", # Name of the model
        target="Label", # Optional. target sshould be a column of validate_df. Pass this parameter only if validate_df is being passed
        classification_labels=[0, 1] # List of the classification labels of your prediction
    )
