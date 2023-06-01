import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
from sklearn import model_selection
import tensorflow_text # noqa

from giskard.client.giskard_client import GiskardClient
from giskard import TensorFlowModel, Dataset

import requests_mock
import re
import tests.utils

tfhub_handle_preprocess = hub.load("https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")
tfhub_handle_preprocess = hub.KerasLayer(
    "https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")
tfhub_handle_encoder = hub.KerasLayer(
    "https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-128_A-2/2",
    trainable=True)


def test_text_classification_tfhub():

    data_filtered = pd.read_csv('tests/tensorflow/test_text_classification_tfhub.csv').dropna(axis=0)

    classification_labels_mapping = {'REGULATION': 0, 'INTERNAL': 1, 'CALIFORNIA CRISIS': 2, 'INFLUENCE': 3}

    y = data_filtered['Target'].map(classification_labels_mapping)
    x = data_filtered['Content']
    x_train, x_test, y_train, y_test = model_selection.train_test_split(x, y,
                                                                        test_size=0.20, random_state=30, stratify=y)

    test_df = pd.DataFrame(list(zip(list(x_test), list(y_test))), columns=["Content", "Target"])

    def build_classifier_model():

        text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
        preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess, name='preprocessing')
        encoder_inputs = preprocessing_layer(text_input)
        encoder = hub.KerasLayer(tfhub_handle_encoder, trainable=True, name='BERT_encoder')
        outputs = encoder(encoder_inputs)
        net = outputs['pooled_output']
        net = tf.keras.layers.Dropout(0.1)(net)
        net = tf.keras.layers.Dense(4, activation='softmax', name='classifier')(net)
        return tf.keras.Model(inputs=text_input, outputs=net)

    model = build_classifier_model()

    my_model = TensorFlowModel(name="Tensorflow_text_classification_tfhub",
                               clf=model,
                               feature_names=['Content'],
                               model_type="classification",
                               classification_labels=['0', '1', '2', '3'])

    # defining the giskard dataset
    my_test_dataset = Dataset(test_df.head(), name="test dataset", target="Target", cat_columns=['Week_day', 'Month'])

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")

    with requests_mock.Mocker() as m:
        m.register_uri(requests_mock.POST, artifact_url_pattern)
        m.register_uri(requests_mock.POST, models_url_pattern)
        m.register_uri(requests_mock.GET, settings_url_pattern)

        url = "http://giskard-host:12345"
        token = "SECRET_TOKEN"
        client = GiskardClient(url, token)
        my_model.upload(client, 'test-project', my_test_dataset)

        tests.utils.match_model_id(my_model.id)
        tests.utils.match_url_patterns(m.request_history, artifact_url_pattern)
        tests.utils.match_url_patterns(m.request_history, models_url_pattern)
