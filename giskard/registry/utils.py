import inspect
import pickle

import cloudpickle


def dump_by_value(obj, f):
    module = inspect.getmodule(obj)

    if module:
        # Shall we register the root module?
        # Will currently fail if test from module.test import from module.utils
        cloudpickle.register_pickle_by_value(module)

    cloudpickle.dump(obj, f, protocol=pickle.DEFAULT_PROTOCOL)
