import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

from giskard.datasets import Dataset
from giskard.models.automodel import Model
from giskard.models.base.serialization import CloudpickleSerializableModel
from tests.registry.module_utils import PythonFile, PythonModule, TmpModule


@mock.patch("giskard.models.base.serialization.cloudpickle.dump")
def test_save_model_raises_error_if_cloudpickle_fails(dump_mock):
    m = mock.MagicMock()
    dump_mock.side_effect = ValueError()
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            CloudpickleSerializableModel.save_model(m, tmpdir)


def test_load_model_raises_error_if_cloudpickle_fails():
    with pytest.raises(ValueError):
        CloudpickleSerializableModel.load_model("model_that_does_not_exist")


SINGLE_FILE_MODULE = PythonModule(
    module_name="my_mocked_module",
    init_content="""
def prediction_function(df):
  return df['input']
    """,
    files=[],
)

MULTIPLE_FILES_MODULE = PythonModule(
    module_name="my_mocked_module",
    init_content="""
from .tests.test import prediction_function

__all__ = [
    "prediction_function"
]
    """,
    files=[
        PythonFile(
            relative_path=Path("tests") / "test.py",
            content="""
from ..utils.test_utils import _do_predict

def prediction_function(df):
  return _do_predict(df)
            """,
        ),
        PythonFile(
            relative_path=Path("utils") / "test_utils.py",
            content="""
def _do_predict(df):
  return df['input']
            """,
        ),
    ],
)


@pytest.mark.parametrize(
    "module_def",
    [SINGLE_FILE_MODULE, MULTIPLE_FILES_MODULE],
)
def test_load_model_from_external_module(module_def):
    with tempfile.TemporaryDirectory() as tmp_test_folder:
        with TmpModule(module_def) as module:
            model = Model(
                module.prediction_function,
                model_type="text_generation",
                name="Mock",
                description="Mock",
                feature_names=["input"],
            )
            model.save(tmp_test_folder)

        del module

        model = Model.load(Path(tmp_test_folder))
        inputs = ["test", "input"]
        dataset = Dataset(pd.DataFrame({"input": inputs}))
        assert list(model.predict(dataset).raw_prediction) == inputs
