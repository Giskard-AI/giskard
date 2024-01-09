import tempfile
from pathlib import Path

import pytest

import giskard
from tests.registry.utils import PythonFile, PythonModule, TmpModule

SINGLE_FILE_MODULE = PythonModule(
    module_name="my_mocked_module",
    init_content="""
import giskard

def _do_test():
  return True

@giskard.test()
def my_test():
  return _do_test()
    """,
    files=[],
)

MULTIPLE_FILES_MODULE = PythonModule(
    module_name="my_mocked_module",
    init_content="""
from .tests.test import my_test

__all__ = [
    "my_test"
]
    """,
    files=[
        PythonFile(
            relative_path=Path("tests") / "test.py",
            content="""
import giskard
from ..utils.test_utils import _do_test

@giskard.test()
def my_test():
  return _do_test()
            """,
        ),
        PythonFile(
            relative_path=Path("utils") / "test_utils.py",
            content="""
def _do_test():
  return True
            """,
        ),
    ],
)


@pytest.mark.parametrize(
    "module_def",
    [SINGLE_FILE_MODULE, MULTIPLE_FILES_MODULE],
)
def test_load_external_module(module_def):
    with tempfile.TemporaryDirectory() as tmp_test_folder:
        with TmpModule(module_def) as module:
            assert module.my_test().execute()

            module.my_test.save(tmp_test_folder)
            meta = module.my_test.meta

        del module

        my_test = giskard.GiskardTest.load(Path(tmp_test_folder), meta.uuid, meta)
        assert my_test().execute()
