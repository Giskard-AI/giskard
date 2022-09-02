import logging
from io import BytesIO

import cloudpickle
import pandas as pd
import time
from zstandard import ZstdDecompressor
from zstandard import decompress

from generated.ml_worker_pb2 import SerializedGiskardModel, SerializedGiskardDataset
from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from ml_worker.utils.logging import timer


@timer()
def deserialize_model(serialized_model: SerializedGiskardModel) -> GiskardModel:
    deserialized_model = GiskardModel(
        cloudpickle.load(ZstdDecompressor().stream_reader(serialized_model.serialized_prediction_function)),
        model_type=serialized_model.model_type,
        classification_threshold=serialized_model.threshold.value if serialized_model.HasField('threshold') else None,
        feature_names=list(serialized_model.feature_names),
        classification_labels=list(serialized_model.classification_labels)
    )

    return deserialized_model


@timer()
def deserialize_dataset(serialized_dataset: SerializedGiskardDataset) -> GiskardDataset:
    deserialized_dataset = GiskardDataset(
        df=pd.read_csv(
            BytesIO(decompress(serialized_dataset.serialized_df)),
            keep_default_na=False,
            na_values=["_GSK_NA_"]
        ),
        target=serialized_dataset.target,
        feature_types=dict(serialized_dataset.feature_types),
        column_types=dict(serialized_dataset.column_types)
    )

    return deserialized_dataset
