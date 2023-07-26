from typing import get_args

from giskard.models.pytorch import TorchDType, string_to_torch_dtype


def test_dtypes():
    for t in get_args(TorchDType):
        assert string_to_torch_dtype(t)
