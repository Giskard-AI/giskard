from giskard.models.automodel import AutoModel


def test_sklearn():
    from sklearn.linear_model import LogisticRegression
    from giskard.models.sklearn import SKLearnModel

    model = LogisticRegression()
    kwargs = {"clf": model, "model_type": "classification"}
    my_model = SKLearnModel(**kwargs)
    my_automodel = AutoModel(**kwargs)

    assert my_model.__module__ == my_automodel.__module__


def test_catboost():
    from catboost import CatBoostClassifier
    from giskard.models.catboost import CatboostModel

    model = CatBoostClassifier()
    kwargs = {"clf": model, "model_type": "classification", "classification_labels": [""]}
    my_model = CatboostModel(**kwargs)
    my_automodel = AutoModel(**kwargs)

    assert my_model.__module__ == my_automodel.__module__


def test_huggingface():
    from giskard.models.huggingface import HuggingFaceModel
    from transformers import BertForSequenceClassification
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2"
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    kwargs = {"clf": model, "model_type": "classification"}
    my_model = HuggingFaceModel(**kwargs)
    my_automodel = AutoModel(**kwargs)

    assert my_model.__module__ == my_automodel.__module__


def test_pytorch():
    from .pytorch.test_linear_regression_pytorch_dataframe import FeedforwardNeuralNetModel
    from giskard.models.pytorch import PyTorchModel

    model = FeedforwardNeuralNetModel(1, 1, 1)
    kwargs = {"clf": model, "model_type": "regression"}
    my_model = PyTorchModel(**kwargs)
    my_automodel = AutoModel(**kwargs)

    assert my_model.__module__ == my_automodel.__module__


def test_tensorflow():
    import tensorflow as tf
    from tensorflow import keras
    from giskard.models.tensorflow import TensorFlowModel

    model = tf.keras.Sequential([
        keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(10, activation='softmax')])
    kwargs = {"clf": model, "model_type": "classification"}
    my_model = TensorFlowModel(**kwargs)
    my_automodel = AutoModel(**kwargs)

    assert my_model.__module__ == my_automodel.__module__
