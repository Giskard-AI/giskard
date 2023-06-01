registry = {}


def register(*args):
    """
    Creates an attribute on the method, so it can
    be discovered by the metaclass
    """

    def decorator(f):
        f._register = args
        return f

    return decorator


class RegisteringType(type):
    def __init__(cls, name, bases, attrs):
        print(f"REGISTERING {name}")
        for key, val in attrs.items():
            properties = getattr(val, "_register", None)
            if properties is not None:
                registry[f"{name}.{key}"] = properties


class GiskardTest(metaclass=RegisteringType):
    pass
