import inspect
import pickle
import sys

import cloudpickle


def _register_root_module_by_value(module):
    if not module:
        return

    root_module_name = module.__name__.split(".")[0]

    if root_module_name == "giskard" or root_module_name not in sys.modules:
        return

    cloudpickle.register_pickle_by_value(sys.modules[root_module_name])


def dump_by_value(obj, f, should_register_by_reference=False):
    if not should_register_by_reference:
        _register_root_module_by_value(inspect.getmodule(obj))

    cloudpickle.dump(obj, f, protocol=pickle.DEFAULT_PROTOCOL)
