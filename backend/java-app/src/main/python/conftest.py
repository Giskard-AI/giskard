from glob import glob

pytest_plugins = [
    'tests.' + fixture_file.replace("/", ".").replace(".py", "")
    for fixture_file in glob("fixtures/**/*.py", recursive=True)
]
