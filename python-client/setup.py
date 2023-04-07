import os
import re
from distutils.dir_util import mkpath
from distutils.errors import DistutilsFileError

import pkg_resources
from setuptools import setup, Command
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
    def copy_tree_dist(  # noqa: C901
            src,
            dst,
            preserve_mode=1,
            preserve_times=1,
            preserve_symlinks=0,
            update=0,
            verbose=1,
            dry_run=0,
    ):
        """Copy an entire directory tree 'src' to a new location 'dst'.

        Both 'src' and 'dst' must be directory names.  If 'src' is not a
        directory, raise DistutilsFileError.  If 'dst' does not exist, it is
        created with 'mkpath()'.  The end result of the copy is that every
        file in 'src' is copied to 'dst', and directories under 'src' are
        recursively copied to 'dst'.  Return the list of files that were
        copied or might have been copied, using their output name.  The
        return value is unaffected by 'update' or 'dry_run': it is simply
        the list of all files under 'src', with the names changed to be
        under 'dst'.

        'preserve_mode' and 'preserve_times' are the same as for
        'copy_file'; note that they only apply to regular files, not to
        directories.  If 'preserve_symlinks' is true, symlinks will be
        copied as symlinks (on platforms that support them!); otherwise
        (the default), the destination of the symlink will be copied.
        'update' and 'verbose' are the same as for 'copy_file'.
        """

        if not dry_run and not os.path.isdir(src):
            raise DistutilsFileError("cannot copy tree '%s': not a directory" % src)
        try:
            names = os.listdir(src)
        except OSError as e:
            if dry_run:
                names = []
            else:
                raise DistutilsFileError(
                    "error listing files in '{}': {}".format(src, e.strerror)
                )

        if not dry_run:
            mkpath(dst, verbose=verbose)

        outputs = []

        for n in names:
            src_name = os.path.join(src, n)
            dst_name = os.path.join(dst, n)

            if n.startswith('.nfs'):
                # skip NFS rename files
                continue

            if preserve_symlinks and os.path.islink(src_name):
                link_dest = os.readlink(src_name)
                if verbose >= 1:
                    print("linking %s -> %s", dst_name, link_dest)
                if not dry_run:
                    os.symlink(link_dest, dst_name)
                outputs.append(dst_name)

            elif os.path.isdir(src_name):
                outputs.extend(
                    InstallLibCommand.copy_tree_dist(
                        src_name,
                        dst_name,
                        preserve_mode,
                        preserve_times,
                        preserve_symlinks,
                        update,
                        verbose=verbose,
                        dry_run=dry_run,
                    )
                )
            else:
                print(f"HOHO {src_name} -->> {dst_name}")
                from distutils.file_util import copy_file
                copy_file(
                    src_name,
                    dst_name,
                    preserve_mode,
                    preserve_times,
                    update,
                    verbose=verbose,
                    dry_run=dry_run,
                )
                outputs.append(dst_name)

        return outputs

    #
    #
    def copy_tree(
            self, infile, outfile,
            preserve_mode=1, preserve_times=1, preserve_symlinks=0, level=1
    ):
        assert preserve_mode and preserve_times and not preserve_symlinks
        exclude = self.get_exclusions()

        print(f"ABA copy_tree infile={infile}, outfile={outfile}")
        if not exclude:
            return InstallLibCommand.copy_tree_dist(infile, outfile)


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
