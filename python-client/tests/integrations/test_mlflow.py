import mlflow
import pytest

def test_sklearn():
    from giskard import demo
    model, df = demo.titanic()
    mlflow.end_run()
    mlflow.start_run()
    model_uri = mlflow.sklearn.log_model(model, "sklearn_model", pyfunc_predict_fn="predict_proba").model_uri

    mlflow.evaluate(
        model=model_uri,
        model_type="classifier",
        data=df,
        targets="Survived",
        evaluators="giskard",
        evaluator_config={"classification_labels": ["no", "yes"]}
    )
    mlflow.end_run()


@pytest.mark.skip(reason="find a faster example")
def test_tensorflow():
    import pandas as pd
    import tensorflow as tf
    from tensorflow.keras import layers
    from pathlib import Path
    from keras.utils import text_dataset_from_directory, get_file

    batch_size = 32
    seed = 42

    dataset = get_file(
        "aclImdb",
        "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz",
        untar=True,
        cache_dir=Path.home() / ".giskard",
    )

    raw_train_ds = text_dataset_from_directory(
        Path(dataset) / "train", batch_size=batch_size, validation_split=0.2, subset="training", seed=seed
    )
    raw_test_ds = text_dataset_from_directory(Path(dataset) / "test", batch_size=batch_size)

    test_dataset = {"Review": [], "Label": []}
    for text_batch, label_batch in raw_test_ds.take(782):
        for i in range(8):
            test_dataset["Review"].append(text_batch.numpy()[i])
            test_dataset["Label"].append(label_batch.numpy()[i])
        test_df = pd.DataFrame.from_dict(test_dataset)

    max_features = 10000
    sequence_length = 250
    vectorize_layer = tf.keras.layers.TextVectorization(
        standardize="lower_and_strip_punctuation",
        max_tokens=max_features,
        output_mode="int",
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
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=["accuracy"]
    )

    export_model = tf.keras.Sequential([vectorize_layer, model])

    export_model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False), optimizer="adam", metrics=["accuracy"]
    )

    mlflow.start_run()
    model_uri = mlflow.tensorflow.log_model(export_model, "tensorflow_model").model_uri

    mlflow.evaluate(
        model=model_uri,
        model_type="classifier",
        data=test_df,
        targets="Label",
        evaluators="giskard",
        evaluator_config={"classification_labels": [0, 1]}
    )
    mlflow.end_run()
