import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers

import tests.utils
from giskard import Dataset
from giskard.models.tensorflow import TensorFlowModel


def test_text_classification_1d_output(imdb_data):
    raw_train_ds, raw_test_ds = imdb_data

    test_dataset = {'Review': [], 'Label': []}
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
        output_sequence_length=sequence_length,
    )

    # Make a text-only dataset (without labels), then call adapt
    train_text = raw_train_ds.map(lambda x, y: x)
    vectorize_layer.adapt(train_text)

    embedding_dim = 16

    model = tf.keras.Sequential(
        [
            layers.Embedding(max_features + 1, embedding_dim),
            layers.Dropout(0.2),
            layers.GlobalAveragePooling1D(),
            layers.Dropout(0.2),
            layers.Dense(1),
        ]
    )

    model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer='adam', metrics=['accuracy']
    )

    export_model = tf.keras.Sequential([vectorize_layer, model])

    export_model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=['accuracy']
    )

    def FromPandastoTFModelInput(test_df):
        test_dataset = test_df.squeeze(axis=1)
        test_dataset = list(test_dataset)
        return test_dataset

    my_model = TensorFlowModel(
        name="Tensorflow_text_classification",
        model=export_model,
        feature_names=['Review'],
        model_type="classification",
        classification_labels=[0, 1],
        data_preprocessing_function=FromPandastoTFModelInput,
    )

    my_test_dataset = Dataset(test_df.head(), name="test dataset", target="Label")

    tests.utils.verify_model_upload(my_model, my_test_dataset)


def test_text_classification_2d_output(imdb_data):
    raw_train_ds, raw_test_ds = imdb_data

    test_dataset = {'Review': [], 'Label': []}
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
        output_sequence_length=sequence_length,
    )

    # Make a text-only dataset (without labels), then call adapt
    train_text = raw_train_ds.map(lambda x, y: x)
    vectorize_layer.adapt(train_text)

    embedding_dim = 16

    model = tf.keras.Sequential(
        [
            layers.Embedding(max_features + 1, embedding_dim),
            layers.Dropout(0.2),
            layers.GlobalAveragePooling1D(),
            layers.Dropout(0.2),
            layers.Dense(2),
            tf.keras.layers.Softmax(),
        ]
    )

    model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer='adam', metrics=['accuracy']
    )

    export_model = tf.keras.Sequential([vectorize_layer, model])

    export_model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=['accuracy']
    )

    def FromPandastoTFModelInput(test_df):
        test_dataset = test_df.squeeze(axis=1)
        test_dataset = list(test_dataset)
        return test_dataset

    my_model = TensorFlowModel(
        name="Tensorflow_text_classification",
        model=export_model,
        feature_names=['Review'],
        model_type="classification",
        classification_labels=[0, 1],
        data_preprocessing_function=FromPandastoTFModelInput,
    )

    my_test_dataset = Dataset(test_df.head(), name="test dataset", target="Label")

    tests.utils.verify_model_upload(my_model, my_test_dataset)
