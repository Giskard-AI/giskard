import logging
from pprint import pprint

from giskard.ml_worker.testing.registry.registry import tests_registry, load_plugins

logger = logging.getLogger(__name__)

load_plugins()
print('\n'.join(tests_registry.get_all().keys()))

# for k, v in tests.items():
#     try:
#         print(k, v())
#     except BaseException as e:
#         logger.error(f"{k}: {e}")
# module_name = load_module_path.parts[-1]
# spec = importlib.util.spec_from_file_location(
#     module_name,
#     load_module_path / Path("__init__.py")
# )
#
# module = importlib.util.module_from_spec(spec)
# sys.path.append(str(load_module_path))
# sys.modules[module_name] = module
# spec.loader.exec_module(module)
#
# spec = importlib.util.spec_from_file_location("custom_tests", load_module_path.parent / '__init__.py')
# sys.modules["custom_tests"] = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(sys.modules["custom_tests"])

# print('DONE')
