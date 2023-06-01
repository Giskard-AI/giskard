from glob import glob

pytest_plugins = [
    fixture_file.replace("/", ".").replace(".py", "")
    for fixture_file in glob("**/fixtures/**/*.py", recursive=True)
]


def pytest_collection_modifyitems(session, config, items):
    # Only considers functions inside /tests directory as unit tests
    # otherwise test functions in the main part of the repo are also detected
    items[:] = [i for i in items if i.location[0].startswith('tests')]
