from giskard.models import infer_giskard_cls
from giskard.models.catboost import CatboostModel
from giskard.models.function import PredictionFunctionModel
from giskard.models.huggingface import HuggingFaceModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.sklearn import SKLearnModel
from giskard.models.tensorflow import TensorFlowModel


def pytorch_model():
    from torchtext.models import RobertaClassificationHead, XLMR_BASE_ENCODER

    num_classes = 2
    input_dim = 768

    classifier_head = RobertaClassificationHead(num_classes=num_classes, input_dim=input_dim)
    return XLMR_BASE_ENCODER.get_model(head=classifier_head, load_weights=False).to("cpu")


def tensorflow_model():
    import tensorflow as tf
    from tensorflow import keras

    return tf.keras.Sequential(
        [
            keras.layers.Dense(512, activation="relu", input_shape=(784,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(10, activation="softmax"),
        ]
    )


def huggingface_model():
    from transformers import AutoModelForSequenceClassification

    return AutoModelForSequenceClassification.from_pretrained("camembert-base").to("cpu")


def test_infer_giskard_cls(german_credit_raw_model, german_credit_catboost_raw_model):
    giskard_cls = infer_giskard_cls(lambda x: x**2)
    assert giskard_cls == PredictionFunctionModel

    giskard_cls = infer_giskard_cls(german_credit_raw_model)
    assert giskard_cls == SKLearnModel

    giskard_cls = infer_giskard_cls(german_credit_catboost_raw_model)
    assert giskard_cls == CatboostModel

    giskard_cls = infer_giskard_cls(pytorch_model())
    assert giskard_cls == PyTorchModel

    giskard_cls = infer_giskard_cls(tensorflow_model())
    assert giskard_cls == TensorFlowModel

    giskard_cls = infer_giskard_cls(huggingface_model())
    assert giskard_cls == HuggingFaceModel
