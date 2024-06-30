import pytest

from giskard.core.model_validation import validate_model


@pytest.mark.memory_expensive
@pytest.mark.skip(reason="Too memory expensive, to be replaced with smaller one")
def test_sst2_pytorch_upload(sst2_model, sst2_data):
    validate_model(sst2_model, validate_ds=sst2_data)
