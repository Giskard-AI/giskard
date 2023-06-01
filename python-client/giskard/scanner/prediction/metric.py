from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
import pandas as pd
from giskard.models._precooked import PrecookedModel


class OverconfidenceDetector:
    model = None
    dataset = None
    raw, prediction, raw_prediction, probabilities, all_predictions = None, None, None, None, None
    ground_truth = None
    all_proba_with_true_label_proba = None
    cost = None

    def __init__(self, model: BaseModel, dataset: Dataset):
        self.model = model
        self.dataset = dataset.copy()
        if isinstance(model, PrecookedModel):
            self.all_predictions = model._predictions.all_predictions
        else:
            raw, prediction, raw_prediction, probabilities, all_predictions = model.predict(
                self.dataset)
            self.all_predictions = all_predictions[1]
        self.ground_truth = pd.DataFrame(dataset.df[dataset.target])
        self._get_true_label_proba()
        self._detect_issues()

    def _get_true_label_proba(self):
        ground_truth_with_proba = self.ground_truth.join(pd.DataFrame(self.all_predictions))
        true_label_proba = ground_truth_with_proba.apply(lambda x: x[x[self.dataset.target]], axis=1).rename(
            "true_proba")
        self.all_proba_with_true_label_proba = pd.DataFrame(self.all_predictions).join(true_label_proba)

    def _detect_issues(self):
        self.cost = pd.DataFrame(self.all_proba_with_true_label_proba.apply(self._diff, axis=1),
                                 columns=["__gsk__loss"])
        incorrect_only = self.dataset.df.join(self.cost)
        incorrect_only = incorrect_only[incorrect_only["__gsk__loss"] != 0]
        incorrect_only.dropna(subset=["__gsk__loss"], inplace=True)
        # @TODO: Handle this properly once we have support for metadata in datasets
        column_types = self.dataset.column_types.copy()
        column_types["__gsk__loss"] = "numeric"

        self.incorrect_dataset = Dataset(df=incorrect_only,
                                         column_types=column_types,
                                         target=self.dataset.target)

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        diff = abs(max_val - x["true_proba"])
        ############
        # row_as_list.remove(max_val)
        # max_val_m1 = max(row_as_list)
        # diff = abs(max_val - max_val_m1)
        ############
        return diff

    def get_dataset(self):
        return self.incorrect_dataset

    def get_proba_rmse(self):
        # res1=self.incorrect_dataset.df["__gsk__loss"].sum()/len(self.incorrect_dataset.df.index)
        # res2=self.incorrect_dataset.df["__gsk__loss"].mean()
        return self.incorrect_dataset.df["__gsk__loss"].mean()


class BorderlineDetector:
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


# class DataLeakageDetector:
#     model = None
#     dataset = None
#     raw = None
#     num_cols = None
#
#     def __init__(self, model: BaseModel, dataset: Dataset):
#         self.model = model
#         self.dataset = dataset.copy()
#         if isinstance(model, PrecookedModel):
#             self.raw = pd.DataFrame(model._predictions.raw)
#         else:
#             raw, prediction, raw_prediction, probabilities, all_predictions = model.predict(
#                 self.dataset)
#             self.raw = pd.DataFrame(raw[1])
#         _, self.num_cols = self.raw.shape
#         self._detect_issues()
#
#     def _detect_issues(self):
#         df = pd.DataFrame(columns=[str(i) for i in range(self.num_cols)])
#         for row in self.dataset.df.iterrows():
#             res = self.model.model.predict_proba(row)
#             df.loc[len(df.index)] = res
#         self.row_by_row = df
#
#     def run(self):
#         data_leakage_check = self.row_by_row == self.raw
#         return data_leakage_check.mean()