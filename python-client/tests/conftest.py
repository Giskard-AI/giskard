from glob import glob
from pathlib import Path

pytest_plugins = []
for f in glob("**/fixtures/**/*.py", recursive=True):
    path = Path(f)
    pytest_plugins.append('.'.join([*path.parts[:-1], path.stem]))


def pytest_collection_modifyitems(session, config, items):
    # Only considers functions inside /tests directory as unit tests
    # otherwise test functions in the main part of the repo are also detected
    items[:] = [i for i in items if i.location[0].startswith("tests")]
