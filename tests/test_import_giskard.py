import subprocess
from time import time

# As of 17.01.2024. The import of giskard takes about 2.5-3 seconds on a 2021 MacBook Pro.
IMPORT_TIME_THRESHOLD_SECOND = 7


def test_import_giskard():
    start = time()

    # Start subprocess to ensure that giskard is not already imported
    # Average of 10 imports to avoid random issues
    for _ in range(10):
        subprocess.run(["python", "-c", "import giskard"])

    end = time()
    assert (
        end - start
    ) / 10 < IMPORT_TIME_THRESHOLD_SECOND, f"Import of Giskard took {(end - start) / 10} seconds on average (maximum threshold is set to {IMPORT_TIME_THRESHOLD_SECOND} second)"
