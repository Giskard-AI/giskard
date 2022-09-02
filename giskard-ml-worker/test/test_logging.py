import time

from ml_worker.utils.logging import Timer, timer


def test_timer():
    timer = Timer()
    time.sleep(0.1)
    duration = timer.stop()
    assert duration.microseconds / 10 ** 6 >= 0.1


@timer()
def wait():
    time.sleep(0.1)


def test_with_timer():
    wait()
    # timer = Timer("Sleeping for {}")
    # with timer:
    #     time.sleep(0.1)
    # assert timer.message is not None
