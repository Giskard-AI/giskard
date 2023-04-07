import os
import sys
import re
from pathlib import Path
from setuptools import setup, find_namespace_packages, Command
from setuptools.command.build import SubCommand
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        self.run_command("build_proto")
        super().run()


class build_proto(Command, SubCommand):
    build_lib: str

    def initialize_options(self):
        self.build_lib = None
        self.out_path = None
        self.proto_path = Path("..", "common", "proto")
        self.proto_file = "ml-worker.proto"

    def finalize_options(self):
        self.set_undefined_options("build_py", ("build_lib", "build_lib"))
        self.out_path = Path(self.build_lib, "giskard", "ml_worker", "generated")

    def run(self):
        self._generate_proto_files()
        self._fix_import_statements()

    def _generate_proto_files(self):
        from grpc_tools import protoc
        import importlib.resources

        common_protos_ref = importlib.resources.files("grpc_tools").joinpath("_proto")

        with importlib.resources.as_file(common_protos_ref) as common_protos_path:
            command = [
                "grpc_tools.protoc",
                f"--proto_path={self.proto_path}",
                f"--proto_path={common_protos_path}",
                f"--python_out={self.out_path}",
                # f"--pyi_out={out_path}",
                f"--grpc_python_out={self.out_path}",
            ] + [str(self.proto_path.joinpath(self.proto_file))]

            if protoc.main(command) != 0:
                print("ERROR: failed to compile proto file.", file=sys.stderr)

    def _fix_import_statements(self):
        for file_path in self.out_path.glob("**/*.py"):
            with file_path.open("r") as f:
                content = f.read()

            content = re.sub(
                "^import ([^\\. ]*?_pb2)",
                f"import giskard.ml_worker.generated.\g<1>",
                content,
                flags=re.MULTILINE,
            )
            with file_path.open("w") as f:
                f.write(content)

    def get_source_files(self):
        return [str(Path(self.proto_path, self.proto_file))]

    def get_outputs(self):
        return [str(self.out_path)]


setup(
    packages=find_namespace_packages(
        where=".",
        include=["giskard*"],
    ),
    cmdclass={"build_py": build_py, "build_proto": build_proto},
)
