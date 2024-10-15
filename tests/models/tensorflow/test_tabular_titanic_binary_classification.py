import pytest

from giskard import Dataset
from giskard.core.model_validation import validate_model
from giskard.demo import titanic_classification
from giskard.models.tensorflow import TensorFlowModel

tf = pytest.importorskip("tensorflow")


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

    validate_model(my_model, validate_ds=my_test_dataset)
