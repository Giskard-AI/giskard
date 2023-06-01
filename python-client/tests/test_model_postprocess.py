import numpy as np
from unittest.mock import Mock

from giskard import WrapperModel
from giskard.core.core import ModelMeta

def test_postprocess():
    model = Mock(WrapperModel)
    meta = Mock(ModelMeta)
    meta.classification_labels = ["First", "Second"]
    model.meta = meta
    model.model_postprocessing_function = None

    data_prepocessing_function_output = np.array(0.6)
    result = WrapperModel._postprocess(model, data_prepocessing_function_output)

    assert result.ndim == 2
    if WrapperModel.is_binary_classification:
        assert result.shape[1] == 2

    data_prepocessing_function_output = np.array([0.6])
    result = WrapperModel._postprocess(model, data_prepocessing_function_output)

    assert result.ndim == 2
    if WrapperModel.is_binary_classification:
        assert result.shape[1] == 2

    data_prepocessing_function_output = np.array([[0.6],[0.4]])
    result = WrapperModel._postprocess(model, data_prepocessing_function_output)

    assert result.ndim == 2
    if WrapperModel.is_binary_classification:
        assert result.shape[1] == 2
