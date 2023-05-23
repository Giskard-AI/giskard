from ...models.base import BaseModel
from ...datasets.base import Dataset
from ..logger import logger
from giskard.scanner.prediction.metric import OverconfidenceDetector
from giskard.scanner.performance.model_bias_detector import ModelBiasDetector, IssueFinder


class PredictionBiasDetector(ModelBiasDetector):

    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug(
            f"ModelBiasDetector: Running with metrics={self.metrics}, threshold={self.threshold}, method={self.method}"
        )

        # Check if we have enough data to run the scan
        if len(dataset) < 100:
            logger.warning("ModelBiasDetector: Skipping scan because the dataset is too small.")
            return []

        # If the dataset is very large, limit to a subsample
        max_data_size = 10_000_000 // len(model.meta.feature_names)
        if len(dataset) > max_data_size:
            logger.debug(f"ModelBiasDetector: Limiting dataset size to {max_data_size} samples.")
            dataset = dataset.slice(lambda df: df.sample(max_data_size, random_state=42), row_level=False)

        oc = OverconfidenceDetector(model, dataset)
        meta = oc.get_dataset()

        # Find slices
        slices = self._find_slices(meta.select_columns(columns=dataset.df.columns), meta.df["__gsk__loss"])

        # Keep only slices of size at least 5% of the dataset
        slices = [s for s in slices if 0.05 * len(dataset) <= len(dataset.slice(s))]

        # Create issues from the slices
        issues = self._find_issues(slices, model, meta.select_columns(columns=dataset.df.columns))

        return issues
