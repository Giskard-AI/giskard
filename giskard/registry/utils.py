import inspect
import pickle
import sys
import warnings

import cloudpickle


def _register_root_module_by_value(module):
    if not module:
        return None

    root_module_name = module.__name__.split(".")[0]

    if (
        root_module_name == "giskard"
        or root_module_name not in sys.modules
        or root_module_name in cloudpickle.cloudpickle.list_registry_pickle_by_value()
    ):
        return None

    root_module = sys.modules[root_module_name]
    cloudpickle.register_pickle_by_value(root_module)
    return root_module


def dump_by_value(obj, f, should_register_by_reference=False):
    registered_module = None

    if not should_register_by_reference:
        registered_module = _register_root_module_by_value(inspect.getmodule(obj))

    try:
        cloudpickle.dump(obj, f, protocol=pickle.DEFAULT_PROTOCOL)
    except Exception as e:
        # When saving by value fails, fallback with saving reference
        if not should_register_by_reference and registered_module:
            # Unregister module
            cloudpickle.unregister_pickle_by_value(registered_module)
            registered_module = None

            # Dump by reference
            dump_by_value(obj, f, True)
            warnings.warn(
                f"Saving {obj} by reference mode was initiated due to an error. To load the model successfully, please ensure that the object is accessible in the Python module where you intend to load it. If the object is not accessible, loading by reference may fail, resulting in errors during the model loading process."
            )
        else:
            raise e

    if registered_module:
        cloudpickle.unregister_pickle_by_value(registered_module)
