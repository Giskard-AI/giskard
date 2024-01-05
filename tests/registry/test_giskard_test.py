import importlib.util
import os
import sys
import tempfile
from pathlib import Path

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
