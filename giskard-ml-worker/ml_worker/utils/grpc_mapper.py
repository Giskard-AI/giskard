from io import BytesIO

import cloudpickle
import pandas as pd
from zstandard import ZstdDecompressor
from zstandard import decompress

from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from generated.ml_worker_pb2 import SerializedGiskardModel, SerializedGiskardDataset


def deserialize_model(serialized_model: SerializedGiskardModel) -> GiskardModel:
    return GiskardModel(
        cloudpickle.load(ZstdDecompressor().stream_reader(serialized_model.serialized_prediction_function)),
        model_type=serialized_model.model_type,
        classification_threshold=serialized_model.threshold.value if serialized_model.HasField('threshold') else None,
        feature_names=list(serialized_model.feature_names),
        classification_labels=list(serialized_model.classification_labels)
    )


def deserialize_dataset(serialized_dataset: SerializedGiskardDataset) -> GiskardDataset:
    return GiskardDataset(
        df=pd.read_csv(BytesIO(decompress(serialized_dataset.serialized_df))),
        target=serialized_dataset.target,
        feature_types=dict(serialized_dataset.feature_types),
        column_types=dict(serialized_dataset.column_types)
    )
