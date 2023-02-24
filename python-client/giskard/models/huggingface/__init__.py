import logging

from giskard.models.sklearn import SKLearnModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.tensorflow import TensorFlowModel
from giskard.core.model import MLFlowBasedModel

logger = logging.getLogger(__name__)


class HuggingFaceModel:
    def __new__(cls, *args, **kw):
        if 'sklearn' in str(type(kw['clf'])):
            return SKLearnModel(**kw)

        elif 'torch' in str(type(kw['clf'])):
            return PyTorchModel(**kw)

        elif 'keras' in str(type(kw['clf'])):
            return TensorFlowModel(**kw)