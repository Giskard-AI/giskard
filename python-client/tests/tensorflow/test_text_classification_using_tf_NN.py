import os
import shutil
import tensorflow as tf
import pandas as pd
from tensorflow.keras import layers

from giskard.client.giskard_client import GiskardClient
from giskard import TensorFlowModel, Dataset

import re
import httpretty
import tests.utils

data_url = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"

dataset = tf.keras.utils.get_file("aclImdb_v1", data_url,
                                  untar=True, cache_dir='.',
                                  cache_subdir='')

@httpretty.activate(verbose=True, allow_net_connect=False)
def test_text_classification_using_tf_NN():


    dataset_dir = os.path.join(os.path.dirname(dataset), 'aclImdb')
    train_dir = os.path.join(dataset_dir, 'train')

    sample_file = os.path.join(train_dir, 'pos/1181_9.txt')

    remove_dir = os.path.join(train_dir, 'unsup')
    shutil.rmtree(remove_dir)

    batch_size = 32
    seed = 42

    raw_test_ds = tf.keras.utils.text_dataset_from_directory(
        'aclImdb/test',
        batch_size=batch_size)

    test_dataset = {'Review':[], 'Label':[]}
    for text_batch, label_batch in raw_test_ds.take(782):
      for i in range(8):
        test_dataset['Review'].append(text_batch.numpy()[i])
        test_dataset['Label'].append(label_batch.numpy()[i])
      test_df = pd.DataFrame.from_dict(test_dataset)

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
        'aclImdb/train',
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
      layers.Dense(2),
      tf.keras.layers.Softmax()
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
        test_dataset= test_df.squeeze(axis=1)
        test_dataset = list(test_dataset)
        return test_dataset

    my_model = TensorFlowModel(name="Tensorflow_text_classification",
                            clf=export_model,
                            feature_names=['Review'],
                            model_type="classification",
                            classification_labels=['0', '1'],
                            data_preprocessing_function=FromPandastoTFModelInput)

    # defining the giskard dataset
    my_test_dataset = Dataset(test_df.head(), name="test dataset", target="Label")

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")

    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, models_url_pattern)
    httpretty.register_uri(httpretty.GET, settings_url_pattern)

    client = GiskardClient(url, token)
    # enron = client.create_project('test-project', "Email Classification", "Email Classification")
    my_model.upload(client, 'test-project', my_test_dataset)

    tests.utils.match_model_id(my_model.id)
    tests.utils.match_url_patterns(httpretty.latest_requests(), artifact_url_pattern)
    tests.utils.match_url_patterns(httpretty.latest_requests(), models_url_pattern)