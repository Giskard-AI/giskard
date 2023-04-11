import os
import re

import pkg_resources
from pathlib import Path
from setuptools import setup, Command
from setuptools.command.build import SubCommand
from setuptools.command.build_py import build_py


class GrpcTool(Command):
    user_options = []

    def initialize_options(self):
        self.build_lib = None
        self.out_path = None
        self.proto_path = Path("..", "common", "proto")
        self.proto_file = "ml-worker.proto"

    def finalize_options(self):
        self.set_undefined_options("build_py", ("build_lib", "build_lib"))
        self.out_path = Path(self.build_lib, "giskard", "ml_worker", "generated")

    def fix_paths(self, path):
        for dirpath, dirs, files in os.walk(path):
            for filename in files:
                print(f"Generated file: {dirpath}/{filename}")
                if not filename.endswith(".py"):
                    continue
                fname = os.path.join(dirpath, filename)
                with open(fname) as rfile:
                    content = rfile.read()
                    content = re.sub(
                        "^import ([^\\. ]*?_pb2)",
                        f"import giskard.ml_worker.generated.\g<1>",
                        content,
                        flags=re.MULTILINE,
                    )
                    with open(fname, "w") as wfile:
                        wfile.write(content)
                    print(f"Fixed {fname}")

    def run(self):
        print("Running grpc_tools.protoc")
        import grpc_tools.protoc

        self.out_path.mkdir(parents=True, exist_ok=True)

        proto_include = pkg_resources.resource_filename("grpc_tools", "_proto")

        cmd = [
            "grpc_tools.protoc",
            f"-I{proto_include}",
            f"-I{self.proto_path}",
            f"--python_out={self.out_path}",
            f"--grpc_python_out={self.out_path}",
        ]
        try:
            import importlib

            importlib.import_module("mypy_protobuf")
            cmd += [f"--mypy_out={self.out_path}", f"--mypy_grpc_out={self.out_path}"]
        except Exception:
            print("mypy-protobuf isn't installed or 'import mypy_protobuf' didn't work")
        cmd.append(f"ml-worker.proto")

        print(f"Running: {' '.join(cmd)}")
        grpc_tools.protoc.main(cmd)

        self.fix_paths(self.out_path)

    def get_source_files(self):
        return [str(Path(self.proto_path, self.proto_file))]

    def get_outputs(self):
        return [str(self.out_path)]


class BuildPyCommand(build_py):
    def run(self) -> None:
        self.run_command("build_grpc")
        super().run()


setup(
    cmdclass={"build_py": BuildPyCommand, "build_grpc": GrpcTool},
)
