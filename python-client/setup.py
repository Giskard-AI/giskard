from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    def finalize_options(self) -> None:
        super().finalize_options()


setup(
    cmdclass={"build_py": BuildPyCommand},
)
