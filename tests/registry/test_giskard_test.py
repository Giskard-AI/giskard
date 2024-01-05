import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

import giskard


def test_load_external_module():
    try:
        with open("my_mocked_module.py", "w") as f:
            f.write(
                """
import giskard

def _do_test():
  return True

@giskard.test()
def my_test():
  return _do_test()

"""
            )

        spec = importlib.util.spec_from_file_location("my_mocked_module", "my_mocked_module.py")
        my_mocked_module = importlib.util.module_from_spec(spec)
        sys.modules["my_mocked_module"] = my_mocked_module
        spec.loader.exec_module(my_mocked_module)

        with tempfile.TemporaryDirectory() as tmpdirname:
            assert my_mocked_module.my_test().execute()

            my_mocked_module.my_test.save(tmpdirname)
            meta = my_mocked_module.my_test.meta

            # Unimport my_mocked_module
            del sys.modules["my_mocked_module"]
            del my_mocked_module
            os.remove("my_mocked_module.py")

            my_test = giskard.GiskardTest.load(Path(tmpdirname), meta.uuid, meta)
            assert my_test().execute()
    finally:
        if Path("my_mocked_module.py").exists():
            os.remove("my_mocked_module.py")


@pytest.mark.skip(reason="Should we pickle whole module by value?")
def test_load_external_module_multiple_levels():
    try:
        with open("tests.py", "w") as f, open("utils.py", "w") as f_utils:
            f_utils.write(
                """
def do_test():
  return True

"""
            )
            f.write(
                """
import giskard
from my_mocked_module.utils import do_test

@giskard.test()
def my_test():
  return do_test()

"""
            )

        utils_spec = importlib.util.spec_from_file_location("my_mocked_module.utils", "utils.py")
        my_mocked_module_utils = importlib.util.module_from_spec(utils_spec)
        sys.modules["my_mocked_module.utils"] = my_mocked_module_utils
        utils_spec.loader.exec_module(my_mocked_module_utils)

        tests_spec = importlib.util.spec_from_file_location("my_mocked_module.tests", "tests.py")
        my_mocked_module_tests = importlib.util.module_from_spec(tests_spec)
        sys.modules["my_mocked_module.tests"] = my_mocked_module_tests
        tests_spec.loader.exec_module(my_mocked_module_tests)

        with tempfile.TemporaryDirectory() as tmpdirname:
            assert my_mocked_module_tests.my_test().execute()

            my_mocked_module_tests.my_test.save(tmpdirname)
            meta = my_mocked_module_tests.my_test.meta

            # Unimport my_mocked_module
            del sys.modules["my_mocked_module.tests"]
            del sys.modules["my_mocked_module.utils"]
            del my_mocked_module_tests
            del my_mocked_module_utils
            os.remove("tests.py")
            os.remove("utils.py")

            my_test = giskard.GiskardTest.load(Path(tmpdirname), meta.uuid, meta)
            assert my_test().execute()
    finally:
        if Path("utils.py").exists():
            os.remove("utils.py")
        if Path("tests.py").exists():
            os.remove("tests.py")
