from typing import List, Union

import importlib.util
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PythonFile:
    relative_path: Path
    content: str


@dataclass
class PythonModule:
    module_name: str
    init_content: str
    files: List[PythonFile]


def _write_file(dir: Path, file: Union[str, Path], content: str):
    os.makedirs(os.path.dirname(dir / file), exist_ok=True)
    with open(dir / file, "w", encoding="utf-8") as f:
        f.write(content)


class TmpModule(object):
    def __init__(self, module_def: PythonModule):
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
