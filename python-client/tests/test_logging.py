import time

import pytest

from giskard.ml_worker.utils.logging import Timer


def test_timer():
    timer = Timer()
    time.sleep(0.1)
    duration = timer.stop()
    assert duration.microseconds == pytest.approx(0.1 * 10**6, 0.10)
