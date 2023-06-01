from sklearn.cluster import KMeans
from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
import pandas as pd
from statistics import mean

import numpy as np


class PredictionIssueDetector:
    model = None
    dataset = None
    prediction_results = None
    kmeans = None

    def __init__(self, model: BaseModel, dataset: Dataset):
        self.model = model
        self.dataset = dataset
        self.prediction_results = self.model.predict(self.dataset)

    def detect_issues(self):
        raw, prediction, raw_prediction, probabilities, all_predictions = self.prediction_results
        all_pred_with_diff = pd.DataFrame(all_predictions[1]).copy()
        col = all_pred_with_diff.columns
        all_pred_with_diff["mult"] = all_pred_with_diff.apply(self._diff, axis=1)
        all_pred_with_diff.drop(columns=col, inplace=True)

        self.kmeans = self.kmeans.fit(all_pred_with_diff)

        all_pred_with_diff["cluster"] = self.kmeans.labels_

        self.all_pred_with_diff = all_pred_with_diff

        return self.all_pred_with_diff


class OverConfidence(PredictionIssueDetector):
    kmeans = KMeans(n_clusters=2, random_state=0)

    def run(self):
        clusterised = self.detect_issues()
        self._cluster_selection()
        correctness = self.check_incorrect_results()
        overconfidence_df = clusterised[correctness]
        overconfidence_df = overconfidence_df[overconfidence_df.cluster == 1]
        self.overconfidence_results = overconfidence_df

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        row_as_list.remove(max_val)
        mean_val = mean(row_as_list)
        diff = abs(max_val - mean_val)
        return diff

    def _cluster_selection(self):
        c1 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 0]["mult"].mean()
        c2 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 1]["mult"].mean()
        cluster_sorted = sorted([[c1, 0], [c2, 1]], key=lambda l: l[0])
        self.all_pred_with_diff["cluster"] = self.all_pred_with_diff["cluster"].map({cluster_sorted[0][1]: 0,
                                                                                     cluster_sorted[1][1]: 1})

    def check_incorrect_results(self):
        raw, prediction, raw_prediction, probabilities, all_predictions = self.prediction_results
        is_incorrect = prediction[1] != self.dataset.df[self.dataset.target]
        return is_incorrect


class Borderline(PredictionIssueDetector):
    kmeans = KMeans(n_clusters=11, random_state=0, init=np.array([[0],
                                                                  [.1],
                                                                  [.2],
                                                                  [.3],
                                                                  [.4],
                                                                  [.5],
                                                                  [.6],
                                                                  [.7],
                                                                  [.8],
                                                                  [.9],
                                                                  [1]]))

    def run(self):
        clusterised = self.detect_issues()
        self._cluster_selection()
        self.borderline_results = clusterised[clusterised.cluster == 0]

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        min_val = min(row_as_list)
        diff = abs(max_val - min_val)
        return diff  # Between 1 and inf

    def _cluster_selection(self):
        c1 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 0]["mult"].mean()
        c2 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 1]["mult"].mean()
        c3 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 2]["mult"].mean()
        c4 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 3]["mult"].mean()
        c5 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 4]["mult"].mean()
        c6 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 5]["mult"].mean()
        c7 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 6]["mult"].mean()
        c8 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 7]["mult"].mean()
        c9 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 8]["mult"].mean()
        c10 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 9]["mult"].mean()
        c11 = self.all_pred_with_diff[self.all_pred_with_diff['cluster'] == 10]["mult"].mean()

        cluster_sorted = sorted([[c1, 0],
                                 [c2, 1],
                                 [c3, 2],
                                 [c4, 3],
                                 [c5, 4],
                                 [c6, 5],
                                 [c7, 6],
                                 [c8, 7],
                                 [c9, 8],
                                 [c10, 9],
                                 [c11, 10]],
                                key=lambda l: l[0])

        self.all_pred_with_diff["cluster"] = self.all_pred_with_diff["cluster"].map({cluster_sorted[0][1]: 0,
                                                                                     cluster_sorted[1][1]: 1,
                                                                                     cluster_sorted[2][1]: 2,
                                                                                     cluster_sorted[3][1]: 3,
                                                                                     cluster_sorted[4][1]: 4,
                                                                                     cluster_sorted[5][1]: 5,
                                                                                     cluster_sorted[6][1]: 6,
                                                                                     cluster_sorted[7][1]: 7,
                                                                                     cluster_sorted[8][1]: 8,
                                                                                     cluster_sorted[9][1]: 9,
                                                                                     cluster_sorted[10][1]: 10,
                                                                                     })
