from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
import pandas as pd
from giskard.models._precooked import PrecookedModel


class ComputeOverconfidence:
    def __init__(self, model, dataset):
        self.dataset = dataset
        raw, prediction, raw_prediction, probabilities, all_predictions = model.predict(dataset)
        all_predictions = all_predictions[1]
        ground_truth = pd.DataFrame(dataset.df[dataset.target])
        ground_truth_with_proba = ground_truth.join(pd.DataFrame(all_predictions))
        true_label_proba = ground_truth_with_proba.apply(lambda x: x[x[dataset.target]], axis=1).rename("true_proba")
        all_proba_with_true_label_proba = pd.DataFrame(all_predictions).join(true_label_proba)
        cost = pd.DataFrame(all_proba_with_true_label_proba.apply(self._diff, axis=1), columns=["__gsk__loss"])
        self.incorrect_only = dataset.df.join(cost)

    def get_dataset(self):
        # self.incorrect_only.dropna(subset=["__gsk__loss"], inplace=True)
        column_types = self.dataset.column_types.copy()
        column_types["__gsk__loss"] = "numeric"
        incorrect_dataset = Dataset(df=self.incorrect_only,
                                    column_types=column_types,
                                    target=self.dataset.target)
        return incorrect_dataset

    def get_metric(self):
        return self.incorrect_only[self.incorrect_only["__gsk__loss"] != 0]["__gsk__loss"].mean()

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        diff = abs(max_val - x["true_proba"])
        return diff

