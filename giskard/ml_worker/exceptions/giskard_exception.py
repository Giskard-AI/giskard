class GiskardException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class GiskardPythonEnvException(GiskardException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class GiskardPythonVerException(GiskardPythonEnvException):
    def __init__(self, cls_name, e, *args: object) -> None:
        super().__init__(
            f"Failed to load '{cls_name}' due to {e.__class__.__name__}.\n"
            "Make sure you are loading it in the environment with matched Python version.",
            *args,
        )


class GiskardPythonDepException(GiskardPythonEnvException):
    def __init__(self, cls_name, e, *args: object) -> None:
        super().__init__(
            f"Failed to load '{cls_name}' due to {e.__class__.__name__}.\n"
            "Make sure you are loading it in the environment with matched dependencies.",
            *args,
        )


def python_env_exception_helper(cls_name, e: Exception):
    if isinstance(e, ValueError):
        if (
            "code expected at most 16 arguments, got 18" in e.args[0]
            or "code() argument 13 must be str, not int" in e.args[0]
        ):
            # Python 3.11 introduces `co_qualname` in code
            # See code in Python 3.10: https://docs.python.org/3.10/library/inspect.html#types-and-members
            # and code in Python 3.11: https://docs.python.org/3.11/library/inspect.html#types-and-members
            return GiskardPythonVerException(cls_name, e)
    # We assume the other cases as the dependency issues
    return GiskardPythonDepException(cls_name, e)
