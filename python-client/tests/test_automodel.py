from giskard.models import make_model
from giskard.core.model import Model


def test_sklearn():
    from sklearn.linear_model import LogisticRegression
    from giskard.models.sklearn import SKLearnModel

    model = LogisticRegression()
    kwargs = {"clf": model, "model_type": "classification"}
    my_automodel1 = make_model(**kwargs)
    assert isinstance(my_automodel1, SKLearnModel)
    my_automodel2 = Model.auto_make(**kwargs)
    assert isinstance(my_automodel2, SKLearnModel)


def test_catboost():
    from catboost import CatBoostClassifier
    from giskard.models.catboost import CatboostModel

    model = CatBoostClassifier()
    kwargs = {"clf": model, "model_type": "classification", "classification_labels": [""], "feature_names": [""]}
    my_automodel1 = make_model(**kwargs)
    assert isinstance(my_automodel1, CatboostModel)
    my_automodel2 = Model.auto_make(**kwargs)
    assert isinstance(my_automodel2, CatboostModel)


def test_huggingface():
    from giskard.models.huggingface import HuggingFaceModel
    from transformers import BertForSequenceClassification
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2"
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    kwargs = {"clf": model, "model_type": "classification"}
    my_automodel1 = make_model(**kwargs)
    assert isinstance(my_automodel1, HuggingFaceModel)
    my_automodel2 = Model.auto_make(**kwargs)
    assert isinstance(my_automodel2, HuggingFaceModel)


def test_pytorch():
    from .pytorch.test_linear_regression_pytorch_dataframe import FeedforwardNeuralNetModel
    from giskard.models.pytorch import PyTorchModel

    model = FeedforwardNeuralNetModel(1, 1, 1)
    kwargs = {"clf": model, "model_type": "regression"}
    my_automodel1 = make_model(**kwargs)
    assert isinstance(my_automodel1, PyTorchModel)
    my_automodel2 = Model.auto_make(**kwargs)
    assert isinstance(my_automodel2, PyTorchModel)


def test_tensorflow():
    import tensorflow as tf
    from tensorflow import keras
    from giskard.models.tensorflow import TensorFlowModel

    model = tf.keras.Sequential([
        keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(10, activation='softmax')])
    kwargs = {"clf": model, "model_type": "classification"}
    my_automodel1 = make_model(**kwargs)
    assert isinstance(my_automodel1, TensorFlowModel)
    my_automodel2 = Model.auto_make(**kwargs)
    assert isinstance(my_automodel2, TensorFlowModel)
