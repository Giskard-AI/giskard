import os
import re

import pkg_resources
from setuptools import setup, Command
from setuptools.command.build_py import build_py


class GrpcTool(Command):
    user_options = []
    out_path = 'giskard'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def fix_paths(self):
        for dirpath, dirs, files in os.walk(self.out_path):
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                fname = os.path.join(dirpath, filename)
                with open(fname) as rfile:
                    content = rfile.read()
                    content = re.sub(
                        '^import ([^\\. ]*?_pb2)', f'import giskard.\g<1>',
                        content, flags=re.MULTILINE)
                    with open(fname, 'w') as wfile:
                        wfile.write(content)
                    print(f'Fixed {fname}')

    def run(self):
        print("Running grpc_tools.protoc")
        import grpc_tools.protoc

        os.makedirs(self.out_path, exist_ok=True)
        proto_path = '../common/proto'
        proto_include = pkg_resources.resource_filename('grpc_tools', '_proto')

        grpc_tools.protoc.main([
            'grpc_tools.protoc',
            f'-I{proto_include}',
            f'-I{proto_path}',
            f'--python_out={self.out_path}',
            f'--grpc_python_out={self.out_path}',
            f'ml-worker.proto'
        ])
        self.fix_paths()


class BuildPyCommand(build_py):
    def run(self):
        self.run_command('grpc')
        super(BuildPyCommand, self).run()


setup(
    cmdclass={
        "build_py": BuildPyCommand,
        "grpc": GrpcTool
    },

)
