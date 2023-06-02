import random

import torch
import pytest
import numpy as np


SEED = 0


@pytest.fixture(autouse=True)
def set_rnd_seed_before_test():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
