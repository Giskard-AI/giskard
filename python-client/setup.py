import os
import re

import pkg_resources
from setuptools import setup, Command
from setuptools.command.build_py import build_py


class GrpcTool(Command):
    user_options = []
    out_path = "giskard/ml_worker/generated"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def fix_paths(path):
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
                        "import giskard.ml_worker.generated.\g<1>",
                        content,
                        flags=re.MULTILINE,
                    )
                    with open(fname, "w") as wfile:
                        wfile.write(content)
                    print(f"Fixed {fname}")

    def run(self):
        print("Running grpc_tools.protoc")
        import grpc_tools.protoc

        os.makedirs(self.out_path, exist_ok=True)
        proto_path = "../common/proto"
        proto_include = pkg_resources.resource_filename("grpc_tools", "_proto")

        cmd = [
            "grpc_tools.protoc",
            f"-I{proto_include}",
            f"-I{proto_path}",
            f"--python_out={self.out_path}",
            f"--grpc_python_out={self.out_path}",
        ]
        try:
            import importlib

            importlib.import_module("mypy_protobuf")
            cmd += [f"--mypy_out={self.out_path}", f"--mypy_grpc_out={self.out_path}"]
        except Exception:
            print("mypy-protobuf isn't installed or 'import mypy_protobuf' didn't work")
        cmd.append("ml-worker.proto")
        print(f"Running: {' '.join(cmd)}")
        grpc_tools.protoc.main(cmd)

        self.fix_paths(self.out_path)


class BuildPyCommand(build_py):
    def finalize_options(self) -> None:
        super().finalize_options()
        self.run_command("grpc")


setup(
    cmdclass={"build_py": BuildPyCommand, "grpc": GrpcTool},
)
