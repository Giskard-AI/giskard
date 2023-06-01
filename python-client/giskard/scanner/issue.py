from ..datasets import Dataset
from ..models.base import BaseModel
from ..ml_worker.testing.registry.slicing_function import SlicingFunction

from typing import Optional


class Issue:
    def __init__(
        self,
        slice_fn: SlicingFunction,
        model: Optional[BaseModel] = None,
        dataset: Optional[Dataset] = None,
        dataset_meta=None,
        test_results=None,
        test_name=None,
    ):
        self.slice_fn = slice_fn
        self.model = model
        self.dataset = dataset
        self.dataset_meta = dataset_meta
        self.test_results = test_results
        self.test_name = test_name

    def __repr__(self):
        return f"<Issue {(self.slice_fn.query.get_all_clauses()[0].to_pandas(), self.test_results.passed, self.test_results.metric,self.test_name)}>"

    @property
    def is_major(self):
        return self.test_results.metric < -0.2

    def examples(self, n=3):
        # @TODO: improve this once we support metadata
        dataset_slice = self.dataset.slice(self.slice_fn)
        df_with_meta = dataset_slice.df.join(self.dataset_meta, how="left")

        examples = df_with_meta.sort_values("__gsk__loss", ascending=False).head(n)
        examples.drop(columns=["__gsk__loss"], inplace=True)
        ex_dataset = Dataset(examples, target=self.dataset.target, column_types=self.dataset.column_types)
        predictions = self.model.predict(ex_dataset).prediction
        examples["predicted_label"] = predictions
        return examples
