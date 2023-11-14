from typing import Dict, Optional

import hashlib
import importlib.util
import inspect
import logging
import os
import sys
import uuid
from pathlib import Path

import cloudpickle

from giskard.core.core import SavableMeta
from giskard.settings import settings


def find_plugin_location():
    return settings.home_dir / "plugins"


logger = logging.getLogger(__name__)
plugins_root = find_plugin_location()


def get_object_uuid(obj) -> str:
    if hasattr(obj, "meta") and hasattr(obj.meta, "uuid"):
        return obj.meta.uuid
    obj_hash = hashlib.sha512(cloudpickle.dumps(obj)).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_OID, obj_hash))


def load_plugins():
    giskard_tests_module = "giskard.testing.tests"
    if giskard_tests_module not in sys.modules:
        importlib.import_module(giskard_tests_module)
    else:
        importlib.reload(sys.modules[giskard_tests_module])

    giskard_functions_module = "giskard.ml_worker.testing.functions"
    if giskard_functions_module not in sys.modules:
        importlib.import_module(giskard_functions_module)
    else:
        importlib.reload(sys.modules[giskard_functions_module])

    if not os.path.exists(plugins_root):
        return
    import_plugin(plugins_root)
    for submodule in os.listdir(str(plugins_root)):
        import_plugin(plugins_root / submodule, plugins_root)


#
def create_module_name(import_path: Path, root: Optional[Path]):
    if root is None:
        return "giskard_plugins"
    else:
        return "giskard_plugins." + ".".join(import_path.with_suffix("").relative_to(root).parts)


def import_plugin(import_path, root=None):
    if not import_path.is_dir() or not os.path.exists((import_path / "__init__.py")) or import_path in sys.path:
        return
    try:
        logger.info(f"Importing plugin: {import_path.name}")
        sys.path.append(str(import_path.absolute()))

        if root is None:
            module_name = create_module_name(import_path, root)
            spec = importlib.util.spec_from_file_location(module_name, import_path / "__init__.py")
            module = importlib.util.module_from_spec(spec)

            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        else:
            importlib.import_module(".".join(import_path.relative_to(root).parts))

    except Exception as e:
        print(e)


class GiskardTestRegistry:
    _tests: Dict[str, SavableMeta] = {}

    def register(self, meta: SavableMeta):
        if meta.uuid not in self._tests:
            self.add_func(meta)
            full_name = f"{meta.full_name} ({meta.uuid})" if hasattr(meta, "full_name") else f"{meta.uuid}"
            logger.debug(f"Registered test function: {full_name}")

    def add_func(self, meta: SavableMeta):
        self._tests[meta.uuid] = meta

    def get_all(self):
        return self._tests

    def get_test(self, test_id):
        return self._tests.get(test_id)


def new_getfile(object, _old_getfile=inspect.getfile):
    if not inspect.isclass(object):
        return _old_getfile(object)

    # Lookup by parent module (as in current inspect)
    if hasattr(object, "__module__"):
        object_ = sys.modules.get(object.__module__)
        if hasattr(object_, "__file__"):
            return object_.__file__

    # If parent module is __main__, lookup by methods (NEW)
    for name, member in inspect.getmembers(object):
        if inspect.isfunction(member) and object.__qualname__ + "." + member.__name__ == member.__qualname__:
            return inspect.getfile(member)

    raise TypeError("Source for {!r} not found".format(object))


# Override getfile to have it working over Jupyter Notebook files
inspect.getfile = new_getfile

tests_registry = GiskardTestRegistry()
