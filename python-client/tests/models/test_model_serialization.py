import tempfile
from unittest import mock

import pytest

from giskard.models.base.serialization import CloudpickleSerializableModel


@mock.patch("giskard.models.base.serialization.cloudpickle.dump")
def test_save_model_raises_error_if_cloudpickle_fails(dump_mock):
    m = mock.MagicMock()
    dump_mock.side_effect = ValueError()
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            CloudpickleSerializableModel.save_model(m, tmpdir)


def test_load_model_raises_error_if_cloudpickle_fails():
    with pytest.raises(ValueError):
        CloudpickleSerializableModel.load_model("model_that_does_not_exist")
