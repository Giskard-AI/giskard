from typing import List, Union

import importlib.util
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

import giskard


@dataclass
class _PythonFile:
    relative_path: Path
    content: str


@dataclass
class _PythonModule:
    module_name: str
    init_content: str
    files: List[_PythonFile]


SINGLE_FILE_MODULE = _PythonModule(
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

MULTIPLE_FILES_MODULE = _PythonModule(
    module_name="my_mocked_module",
    init_content="""
from .tests.test import my_test

__all__ = [
    "my_test"
]
    """,
    files=[
        _PythonFile(
            relative_path=Path("tests") / "test.py",
            content="""
import giskard
from ..utils.test_utils import _do_test

@giskard.test()
def my_test():
  return _do_test()
            """,
        ),
        _PythonFile(
            relative_path=Path("utils") / "test_utils.py",
            content="""
def _do_test():
  return True
            """,
        ),
    ],
)


def _write_file(dir: Path, file: Union[str, Path], content: str):
    os.makedirs(os.path.dirname(dir / file), exist_ok=True)
    with open(dir / file, "w") as f:
        f.write(content)


class _TmpModule(object):
    def __init__(self, module_def: _PythonModule):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.module_def = module_def

    def __enter__(self):
        dir = Path(self.temp_dir.__enter__())

        _write_file(dir, "__init__.py", self.module_def.init_content)
        for file_def in self.module_def.files:
            _write_file(dir, file_def.relative_path, file_def.content)

        spec = importlib.util.spec_from_file_location(self.module_def.module_name, dir / "__init__.py")
        loaded_module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_def.module_name] = loaded_module
        spec.loader.exec_module(loaded_module)

        return loaded_module

    def __exit__(self, type, value, traceback):
        del sys.modules[self.module_def.module_name]
        self.temp_dir.__exit__(type, value, traceback)


@pytest.mark.parametrize(
    "module_def",
    [SINGLE_FILE_MODULE, MULTIPLE_FILES_MODULE],
)
def test_load_external_module(module_def):
    with tempfile.TemporaryDirectory() as tmp_test_folder:
        with _TmpModule(module_def) as module:
            assert module.my_test().execute()

            module.my_test.save(tmp_test_folder)
            meta = module.my_test.meta

        del module

        my_test = giskard.GiskardTest.load(Path(tmp_test_folder), meta.uuid, meta)
        assert my_test().execute()
