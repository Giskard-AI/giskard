import distutils.command.install_lib as orig
import os
import re
import shutil

import pkg_resources
from setuptools import setup, Command
from setuptools.archive_util import UnrecognizedFormat
from setuptools.command.build_py import build_py
from setuptools.command.install_lib import install_lib


class GrpcTool(Command):
    user_options = []
    out_path = 'giskard/ml_worker/generated'

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
                        '^import ([^\\. ]*?_pb2)', f'import giskard.ml_worker.generated.\g<1>',
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
        for r, d, f in os.walk('giskard'):
            for file in f:
                print(f'ABA: {r}/{file}')

        # self.fix_paths()


class InstallLibCommand(install_lib):
    @staticmethod
    def ensure_directory(path):
        """Ensure that the parent directory of `path` exists"""
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)

    @staticmethod
    def unpack_directory(filename, extract_dir, progress_filter):
        """"Unpack" a directory, using the same interface as for archives

        Raises ``UnrecognizedFormat`` if `filename` is not a directory
        """
        if not os.path.isdir(filename):
            raise UnrecognizedFormat("%s is not a directory" % filename)

        paths = {
            filename: ('', extract_dir),
        }
        for base, dirs, files in os.walk(filename):
            src, dst = paths[base]
            for d in dirs:
                paths[os.path.join(base, d)] = src + d + '/', os.path.join(dst, d)
            for f in files:
                target = os.path.join(dst, f)
                target = progress_filter(src + f, target)
                if not target:
                    # skip non-files
                    continue
                InstallLibCommand.ensure_directory(target)
                f = os.path.join(base, f)
                shutil.copyfile(f, target)
                shutil.copystat(f, target)

    def copy_tree(
            self, infile, outfile,
            preserve_mode=1, preserve_times=1, preserve_symlinks=0, level=1
    ):
        assert preserve_mode and preserve_times and not preserve_symlinks
        exclude = self.get_exclusions()

        if not exclude:
            return orig.install_lib.copy_tree(self, infile, outfile)

        # Exclude namespace package __init__.py* files from the output

        from distutils import log

        outfiles = []

        def pf(src, dst):
            if dst in exclude:
                log.warn("Skipping installation of %s (namespace package)",
                         dst)
                return False

            log.info("copying %s -> %s", src, os.path.dirname(dst))
            outfiles.append(dst)
            return dst

        InstallLibCommand.unpack_directory(infile, outfile, pf)
        return outfiles


class BuildPyCommand(build_py):
    def run(self):
        self.run_command('grpc')
        super(BuildPyCommand, self).run()


setup(
    cmdclass={
        "build_py": BuildPyCommand,
        "install_lib": InstallLibCommand,
        "grpc": GrpcTool
    },

)
