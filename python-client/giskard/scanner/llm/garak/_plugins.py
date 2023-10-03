import importlib
import logging


def load_plugin(path, break_on_fail=True):
    """load_plugin takes a path to a plugin class, and attempts to load that class.
    If successful, it returns an instance of that class.

    :param path: The path to the class to be loaded, e.g. "probes.test.Blank"
    :type path: str
    :param break_on_fail: Should we raise exceptions if there are problems with the load?
      (default is True)
    :type break_on_fail: bool
    """
    try:
        category, module_name, plugin_class_name = path.split(".")
    except ValueError:
        if break_on_fail:
            raise ValueError(f'Expected plugin name in format category.module_name.class_name, got "{path}"')
        else:
            return False
    module_path = f"giskard.scanner.llm.garak.{category}.{module_name}"
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        logging.warning(f"Exception failed import of {module_path}")
        if break_on_fail:
            raise ValueError("Didn't successfully import " + module_name)
        else:
            return False

    try:
        plugin_instance = getattr(mod, plugin_class_name)()
    except AttributeError:
        logging.warning(f"Exception failed instantiation of {module_path}.{plugin_class_name}")
        if break_on_fail:
            raise ValueError(f"Plugin {plugin_class_name} not found in {category}.{module_name}")
        else:
            return False
    except Exception:
        # print("error in: module", mod.__name__, "class", plugin_class_name)
        # logging.warning(f"error in: module {mod} class {plugin_class_name}")
        return False

    return plugin_instance
