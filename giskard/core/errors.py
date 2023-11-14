from typing import Optional


class GiskardInstallationError(ImportError):
    functionality: Optional[str]
    flavor: Optional[str]

    def __init__(self, flavor: str = None, functionality: str = None, msg: str = None) -> None:
        self.msg = msg
        if not self.msg:
            self.flavor = flavor or self.flavor
            self.functionality = functionality or self.functionality
            assert self.flavor, "Either giskard package flavor or custom error message should be provided"

            self.msg = (
                f"It seems that you are using Giskard {self.functionality or self.flavor} functionality "
                "but you are missing some required package. Please install Giskard "
                f"with {self.functionality or self.flavor} support with `pip install giskard[{self.flavor}]`."
            )


class GiskardImportError(ImportError):
    def __init__(self, missing_package: str) -> None:
        self.msg = f"The '{missing_package}' Python package is not installed; please execute 'pip install {missing_package}' to obtain it."
