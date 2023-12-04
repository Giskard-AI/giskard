import numpy as np
import requests_mock

from giskard.core.core import SavableMeta
from tests.utils import MockedClient


class MetaWithBool(SavableMeta):
    def to_json(self):
        return {
            **super().to_json(),
            "one_numpy_bool": np.bool_(True),
        }


def test_upload_meta_with_numpy_bool():
    META_URL = "https://localhost:12500/meta"
    meta = MetaWithBool()

    with MockedClient() as (client, mr):
        mr.register_uri(requests_mock.PUT, META_URL, json="")
        assert client.save_meta(META_URL, meta=meta) == meta
