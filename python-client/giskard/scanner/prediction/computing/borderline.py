from giskard.datasets.base import Dataset
import pandas as pd


class ComputeBorderline:
    def __init__(self, model, dataset):
        raw, prediction, raw_prediction, probabilities, all_predictions = model.predict(dataset)
        all_predictions = pd.DataFrame(all_predictions[1])
        cost = pd.DataFrame(all_predictions.apply(self._diff, axis=1), columns=["__gsk__loss"])
        df_merged_with_metric = dataset.df.join(cost)
        # @TODO: Handle this properly once we have support for metadata in datasets
        column_types = dataset.column_types.copy()
        column_types["__gsk__loss"] = "numeric"
        self.gsk_dataset_merged_with_metric = Dataset(df=df_merged_with_metric,
                                                      column_types=column_types,
                                                      target=dataset.target)

    def get_dataset(self):
        return self.gsk_dataset_merged_with_metric

    def get_metric(self):
        return self.gsk_dataset_merged_with_metric.df["__gsk__loss"].mean()

    def _diff(self, x):
        row_as_list = x.values.flatten().tolist()
        max_val = max(row_as_list)
        row_as_list.remove(max_val)
        second_max_val = max(row_as_list)
        diff = abs(max_val - second_max_val)
        return diff
