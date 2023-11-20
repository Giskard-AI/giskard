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
