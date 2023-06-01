import logging
from scipy import stats

from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.tests.performance import test_diff_f1, test_diff_rmse, test_diff_accuracy, \
    test_diff_recall, test_diff_precision


class DataSliceFilter:
    """Selects slices based on their significance."""

    def filter(self, slices):
        raise NotImplementedError()


class InternalTestFilter(DataSliceFilter):

    def __init__(self, model, dataset, test_name=None, threshold=0.1):
        self.dataset = dataset
        self.model = model
        self.threshold = threshold

        if test_name == "f1":
            self.test = test_diff_f1
        if test_name == "accuracy":
            self.test = test_diff_accuracy
        if test_name == "recall":
            self.test = test_diff_recall
        if test_name == "precision":
            self.test = test_diff_precision
        if test_name == "rmse":
            self.test = test_diff_rmse
        if test_name is None:
            self.test = test_diff_f1

    def _diff_test(self, data_slice):
        # Convert slice to Giskard Dataframe
        slice_dataset = Dataset(data_slice.data)
                                # target_col=self.dataset.target,
                                # column_types=self.dataset.column_types

        # Apply the test
        test_res = self.test(
            actual_slice=slice_dataset,
            reference_slice=self.dataset,  # Could exclude slice_dataset for independence
            model=self.model,
            threshold=self.threshold,
        )

        return not test_res.passed

    def filter(self, slices):
        return list(filter(self._diff_test, slices))


class SignificanceFilter(DataSliceFilter):
    def __init__(self, target, p_value=1e-3, alternative="greater"):
        self.p_value = p_value
        self.target = target
        self.alternative = alternative

    def filter(self, slices):
        slices = [s for s in slices if len(s) > 0]

        if len(slices) < 2:
            return []

        # # Kruskal–Wallis to see if there is significant difference in the slices
        # kw_res = stats.kruskal(*[s.data[target].values for s in slices])

        # logging.debug(f"Kruskal–Wallis p_value = {kw_res.pvalue:.2e}")
        # if kw_res.pvalue > 1e-3:
        #     logging.debug(
        #         f"Kruskal–Wallis test signals no significance in the slices, stopping now."
        #     )
        #     return []

        # Mood’s median test to see if there is significant difference in the slices
        mt_pval = stats.median_test(*[s.data[self.target].values for s in slices])[1]

        logging.debug(f"Mood’s median test p_value = {mt_pval:.2e}")
        if mt_pval > 1e-3:
            logging.debug(
                f"Mood’s median test signals no significance in the slices, stopping now."
            )
            return []

        # Paired tests
        return list(filter(self._pairwise_test, slices))

    def _pairwise_test(self, data_slice):
        slice_mean = data_slice.data[self.target].mean()
        bg_mean = data_slice.data_complement[self.target].mean()

        if slice_mean < 1.15 * bg_mean:
            return False

        p_value = stats.brunnermunzel(
            data_slice.data[self.target],
            data_slice.data_complement[self.target],
            alternative=self.alternative,
        ).pvalue

        return p_value <= self.p_value
