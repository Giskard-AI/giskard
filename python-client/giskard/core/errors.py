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
                f"but you are "
                f"missing some required package. Please install Giskard "
                f"with {self.functionality or self.flavor} support "
                f"with `pip install giskard[{self.flavor}]`."
            )
