import pytest

import tests.utils


@pytest.mark.memory_expensive
def test_sst2_pytorch_upload(sst2_model, sst2_data):
    tests.utils.verify_model_upload(sst2_model, sst2_data)
