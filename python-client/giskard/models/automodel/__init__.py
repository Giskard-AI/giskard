from giskard.models.sklearn import SKLearnModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.tensorflow import TensorFlowModel
from giskard.models.huggingface import HuggingFaceModel

class AutoModel:
    def __new__(cls, *args, **kw):
        is_huggingface = "transformers" in kw['clf'].__module__
        is_sklearn = "sklearn" in kw['clf'].__module__
        is_pytorch = "torch" in kw['clf'].__module__
        is_tensorflow = "keras" in kw['clf'].__module__ or "tensorflow" in kw['clf'].__module__

        if is_huggingface:
            return HuggingFaceModel(**kw)
        elif is_sklearn:
            return SKLearnModel(**kw)
        elif is_pytorch:
            return PyTorchModel(**kw)
        elif is_tensorflow:
            return TensorFlowModel(**kw)
        else:
            raise ValueError(
                'We could not infer your model library. We currently only support models from:'
                '- sklearn'
                '- pytorch'
                '- tensorflow'
                '- huggingface'
            )
