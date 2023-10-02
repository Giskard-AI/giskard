import pytest

from giskard.models.utils import fix_seed


@pytest.fixture(autouse=True)
def set_rnd_seed_before_test():
    fix_seed()
