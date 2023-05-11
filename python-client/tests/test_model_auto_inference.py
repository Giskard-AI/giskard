from giskard.models.automodel import Model


def test_sklearn():
    from sklearn.linear_model import LogisticRegression
    from giskard.models.sklearn import SKLearnModel

    my_model = LogisticRegression()
    kwargs = {"model": my_model, "model_type": "classification", "classification_labels": [""]}
    my_automodel = Model(**kwargs)
    assert isinstance(my_automodel, SKLearnModel)


def test_catboost():
    from catboost import CatBoostClassifier
    from giskard.models.catboost import CatboostModel

    my_model = CatBoostClassifier()
    kwargs = {"model": my_model, "model_type": "classification", "classification_labels": [""], "feature_names": [""]}
    my_automodel = Model(**kwargs)
    assert isinstance(my_automodel, CatboostModel)


def test_huggingface():
    from giskard.models.huggingface import HuggingFaceModel
    from transformers import BertForSequenceClassification
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2"
    my_model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    kwargs = {"model": my_model, "model_type": "classification", "classification_labels": [""]}
    my_automodel = Model(**kwargs)
    assert isinstance(my_automodel, HuggingFaceModel)


def test_pytorch():
    from .pytorch.test_linear_regression_pytorch_dataframe import FeedforwardNeuralNetModel
    from giskard.models.pytorch import PyTorchModel

    my_model = FeedforwardNeuralNetModel(1, 1, 1)
    kwargs = {"model": my_model, "model_type": "regression"}
    my_automodel = Model(**kwargs)
    assert isinstance(my_automodel, PyTorchModel)


def test_tensorflow():
    import tensorflow as tf
    from tensorflow import keras
    from giskard.models.tensorflow import TensorFlowModel

    my_model = tf.keras.Sequential([
        keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(10, activation='softmax')])
    kwargs = {"model": my_model, "model_type": "classification", "classification_labels": [""]}
    my_automodel = Model(**kwargs)
    assert isinstance(my_automodel, TensorFlowModel)
