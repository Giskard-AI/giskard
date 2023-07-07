import tensorflow as tf

import tests.utils
from giskard import Dataset
from giskard.demo import titanic_classification
from giskard.models.tensorflow import TensorFlowModel


def test_tabular_titanic_binary_classification():
    df = titanic_classification.get_test_df()
    preprocess, _ = titanic_classification.get_pipeline()

    input_shape = (preprocess(df).shape[-1],)

    model = tf.keras.models.Sequential(
        [
            tf.keras.layers.Dense(128, input_shape=input_shape, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(2, activation="softmax"),
        ]
    )

    my_model = TensorFlowModel(
        model,
        feature_names=df.columns.drop("Survived"),
        model_type="classification",
        classification_labels=["no", "yes"],
        data_preprocessing_function=preprocess,
    )

    my_test_dataset = Dataset(df, target="Survived", name="test dataset")

    assert my_model.predict(my_test_dataset)
    assert my_model.predict(my_test_dataset).raw.shape == (len(df), 2)

    tests.utils.verify_model_upload(my_model, my_test_dataset)
