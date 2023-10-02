import pandas as pd
from mlflow.models import EvaluationArtifact
from zstandard import ZstdDecompressor

from giskard.client.io_utils import save_df


class GiskardDatasetEvaluationArtifact(EvaluationArtifact):
    def _save(self, output_artifact_path):
        with open(output_artifact_path, "wb") as fw:
            uncompressed_bytes = save_df(self._content)
            fw.write(uncompressed_bytes)

    def _load_content_from_file(self, local_artifact_path):
        with open(local_artifact_path, "rb") as ds_stream:
            return pd.read_csv(
                ZstdDecompressor().stream_reader(ds_stream),
                keep_default_na=False,
                na_values=["_GSK_NA_"],
            )


class GiskardScanResultEvaluationArtifact(EvaluationArtifact):
    def _save(self, output_artifact_path):
        self._content.to_html(output_artifact_path)

    def _load_content_from_file(self, local_artifact_path):
        with open(local_artifact_path, "rb") as f:
            return f.read()


class GiskardScanSummaryEvaluationArtifact(GiskardDatasetEvaluationArtifact):
    def _load_content_from_file(self, local_artifact_path):
        with open(local_artifact_path, "rb") as ds_stream:
            return pd.read_csv(
                ZstdDecompressor().stream_reader(ds_stream),
                keep_default_na=False,
            )
