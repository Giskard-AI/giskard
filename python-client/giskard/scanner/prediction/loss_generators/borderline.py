from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
import pandas as pd
from giskard.models._precooked import PrecookedModel


class BorderlineDatasetGenerator:
    model = None
    dataset = None
    all_predictions = None
    cost = None

    def __init__(self, model: BaseModel, dataset: Dataset):
        self.model = model
        self.dataset = dataset.copy()
        if isinstance(model, PrecookedModel):
            self.all_predictions = pd.DataFrame(model._predictions.all_predictions)
        else:
            raw, prediction, raw_prediction, probabilities, all_predictions = model.predict(
                self.dataset)
            self.all_predictions = pd.DataFrame(all_predictions[1])
        self.ground_truth = pd.DataFrame(dataset.df[dataset.target])
        self._detect_issues()

    def _detect_issues(self):
        self.cost = pd.DataFrame(self.all_predictions.apply(self._diff, axis=1),
                                 columns=["__gsk__loss"])
        df_merged_with_metric = self.dataset.df.join(self.cost)
        # incorrect_only = incorrect_only[incorrect_only["__gsk__loss"] != 0]
        # incorrect_only.dropna(subset=["__gsk__loss"],inplace=True)
        # @TODO: Handle this properly once we have support for metadata in datasets
        column_types = self.dataset.column_types.copy()
        column_types["__gsk__loss"] = "numeric"
        self.gsk_dataset_merged_with_metric = Dataset(df=df_merged_with_metric,
                                                      column_types=column_types,
                                                      target=self.dataset.target)

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        row_as_list.remove(max_val)
        second_max_val = max(row_as_list)
        diff = abs(max_val - second_max_val)
        return diff

    def get_dataset(self):
        return self.gsk_dataset_merged_with_metric

    def get_proba_rmse(self):
        # res1=self.incorrect_dataset.df["__gsk__loss"].sum()/len(self.incorrect_dataset.df.index)
        # res2=self.incorrect_dataset.df["__gsk__loss"].mean()
        return self.gsk_dataset_merged_with_metric.df["__gsk__loss"].mean()
