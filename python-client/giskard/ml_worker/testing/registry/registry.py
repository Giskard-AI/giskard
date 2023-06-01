import importlib.util
import inspect
import logging
import os
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

from giskard.settings import expand_env_var, settings


@dataclass
class Model:
    name: str


@dataclass
class Dataset:
    name: str


logger = logging.getLogger(__name__)
plugins_root = Path(expand_env_var(settings.home)) / "plugins"


def _get_plugin_method_full_name(func):
    path_parts = list(Path(inspect.getfile(func)).relative_to(plugins_root).with_suffix("").parts)
    path_parts.insert(0, 'giskard_plugins')
    if '__init__' in path_parts:
        path_parts.remove('__init__')
    path_parts.append(func.__name__)
    return ".".join(path_parts)


def load_plugins():
    giskard_tests_module = "giskard.ml_worker.testing.tests"
    if giskard_tests_module not in sys.modules:
        importlib.import_module(giskard_tests_module)
    else:
        importlib.reload(sys.modules[giskard_tests_module])

    if not os.path.exists(plugins_root):
        logger.info(f"Plugins directory doesn't exist: {plugins_root}")
        return
    import_plugin(plugins_root)
    for submodule in os.listdir(str(plugins_root)):
        import_plugin(plugins_root / submodule, plugins_root)


#
def create_module_name(import_path: Path, root: Optional[Path]):
    if root is None:
        return "giskard_plugins"
    else:
        return "giskard_plugins." + '.'.join(import_path.with_suffix("").relative_to(root).parts)


def import_plugin(import_path, root=None):
    if not import_path.is_dir() or not os.path.exists((import_path / '__init__.py')) or import_path in sys.path:
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
            importlib.import_module('.'.join(import_path.relative_to(root).parts))

    except Exception as e:
        print(e)


@dataclass
class TestFunctionArgument:
    name: str
    type: str
    default: any
    optional: bool


@dataclass
class TestFunction:
    code: str
    id: str
    name: str
    module: str
    doc: str
    module_doc: str
    fn: types.FunctionType
    args: Dict[str, TestFunctionArgument]
    tags: List[str]


def create_test_function_id(func):
    try:
        # is_relative_to is only available from python 3.9
        is_relative = Path(inspect.getfile(func)).relative_to(plugins_root)
    except ValueError:
        is_relative = False
    if is_relative:
        full_name = _get_plugin_method_full_name(func)
    else:
        full_name = f"{func.__module__}.{func.__name__}"
    return full_name


class GiskardTestRegistry:
    _tests: Dict[str, TestFunction] = {}

    def register(self, func: types.FunctionType, name=None, tags=None):
        full_name = create_test_function_id(func)

        if full_name not in self._tests:
            # arg_spec = inspect.getfullargspec(func)
            parameters = inspect.signature(func).parameters
            args_without_type = [p for p in parameters if parameters[p].annotation == inspect.Parameter.empty]

            if len(args_without_type):
                logger.warning(
                    f'Test function definition "{func.__module__}.{func.__name__}" is missing argument type: {", ".join(args_without_type)}')
                return
            func.__module__.rpartition(".")
            func_doc = self._extract_doc(func)

            tags = [] if not tags else tags
            if full_name.partition(".")[0] == 'giskard':
                tags.append("giskard")
            else:
                tags.append("custom")

            code = None
            try:
                code = inspect.getsource(func)
            except Exception as e:
                logger.info(f"Failed to extract test function code {full_name}", e)

            self._tests[full_name] = TestFunction(
                id=full_name,
                code=code,
                name=name or func.__name__,
                tags=tags,
                module=func.__module__,
                doc=func_doc,
                module_doc=inspect.getmodule(func).__doc__.strip() if inspect.getmodule(func).__doc__ else None,
                fn=func,
                args={
                    name: TestFunctionArgument(
                        name=name,
                        type=parameters[name].annotation.__qualname__,
                        optional=parameters[name].default != inspect.Parameter.empty
                                 and parameters[name].default is not None,
                        default=None if parameters[name].default == inspect.Parameter.empty else parameters[
                            name].default
                    )
                    for name in parameters}
            )
            logger.info(f"Registered test function: {full_name}")

    @staticmethod
    def _extract_doc(func):
        if func.__doc__:
            func_doc, _, args_doc = func.__doc__.partition("\n\n\n")
            func_doc = re.sub(r'\n[ \t\n]+', r'\n', func_doc.strip())
        else:
            func_doc = None
        return func_doc

    def get_all(self):
        return self._tests

    def get_test(self, test_id):
        return self._tests.get(test_id)


tests_registry = GiskardTestRegistry()
