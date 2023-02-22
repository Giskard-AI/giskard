import tensorflow as tf
from tensorflow import keras

from giskard.client.giskard_client import GiskardClient
from giskard import TensorFlowModel, Dataset

import requests_mock
import re
import tests.utils

# Define a simple sequential model
def create_model():
    model = tf.keras.Sequential(
        [
            keras.layers.Dense(512, activation="relu", input_shape=(784,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(10, activation="softmax"),
        ]
    )

    model.compile(
        optimizer="adam",
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
    )

    return model


def test_mnist():

    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()

    # Create a basic model instance
    model = create_model()

    train_labels = train_labels[:100]
    # test_labels = test_labels[:100]

    train_images = train_images[:100].reshape(-1, 28 * 28) / 255.0
    # test_images = test_images[:100].reshape(-1, 28 * 28) / 255.0

    # Create and train a new model instance.
    model = create_model()
    model.fit(train_images, train_labels, epochs=1)

    my_model = TensorFlowModel(
        name="TensorFlow_MNIST",
        clf=model,
        model_type="classification",
        classification_labels=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    )

    # defining the giskard dataset
    my_test_dataset = Dataset(train_images, name="dataset")

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")

    with requests_mock.Mocker() as m:
        m.register_uri(requests_mock.POST, artifact_url_pattern)
        m.register_uri(requests_mock.POST, models_url_pattern)
        m.register_uri(requests_mock.GET, settings_url_pattern)

        url = "http://giskard-host:12345"
        token = "SECRET_TOKEN"
        client = GiskardClient(url, token)
        # enron = client.create_project('test-project', "Email Classification", "Email Classification")
        my_model.upload(client, "test-project", my_test_dataset)

        tests.utils.match_model_id(my_model.id)
        tests.utils.match_url_patterns(m.request_history, artifact_url_pattern)
        tests.utils.match_url_patterns(m.request_history, models_url_pattern)
