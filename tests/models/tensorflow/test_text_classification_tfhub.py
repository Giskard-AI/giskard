from pathlib import Path

import pandas as pd
import pytest
from sklearn import model_selection

from giskard import Dataset
from giskard.core.model_validation import validate_model
from giskard.models.tensorflow import TensorFlowModel

tf = pytest.importorskip("tensorflow")
# Use keras 2: https://github.com/tensorflow/hub/issues/903
keras = pytest.importorskip("tf_keras")


@pytest.mark.memory_expensive
def test_text_classification_tfhub():
    hub = pytest.importorskip("tensorflow_hub")
    pytest.importorskip("tensorflow_text")

    tfhub_handle_preprocess = hub.load("https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")
    tfhub_handle_preprocess = hub.KerasLayer("https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")
    tfhub_handle_encoder = hub.KerasLayer(
        "https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-128_A-2/2", trainable=True
    )

    data_filtered = pd.read_csv(Path(__file__).parent / "test_text_classification_tfhub.csv").dropna(axis=0)

    classification_labels_mapping = {"REGULATION": 0, "INTERNAL": 1, "CALIFORNIA CRISIS": 2, "INFLUENCE": 3}

    y = data_filtered["Target"].map(classification_labels_mapping)
    x = data_filtered["Content"]
    x_train, x_test, y_train, y_test = model_selection.train_test_split(
        x, y, test_size=0.20, random_state=30, stratify=y
    )

    test_df = pd.DataFrame(list(zip(list(x_test), list(y_test))), columns=["Content", "Target"])

    def build_classifier_model():
        text_input = keras.layers.Input(shape=(), dtype=tf.string, name="text")
        preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess, name="preprocessing")
        encoder_inputs = preprocessing_layer(text_input)
        encoder = hub.KerasLayer(tfhub_handle_encoder, trainable=True, name="BERT_encoder")
        outputs = encoder(encoder_inputs)
        net = outputs["pooled_output"]
        net = keras.layers.Dropout(0.1)(net)
        net = keras.layers.Dense(4, activation="softmax", name="classifier")(net)
        return keras.Model(inputs=text_input, outputs=net)

    model = build_classifier_model()

    my_model = TensorFlowModel(
        name="Tensorflow_text_classification_tfhub",
        model=model,
        feature_names=["Content"],
        model_type="classification",
        classification_labels=[0, 1, 2, 3],
    )

    # defining the giskard dataset
    my_test_dataset = Dataset(test_df.head(), name="test dataset", target="Target")

    my_model.predict(my_test_dataset)

    validate_model(my_model, validate_ds=my_test_dataset)
