import logging
from scipy import stats

from giskard.datasets import Dataset
from giskard.ml_worker.testing.tests.performance import test_diff_f1


class DataSliceFilter:
    """Selects slices based on their significance."""

    def filter(self, slices):
        raise NotImplementedError()


class InternalTestFilter(DataSliceFilter):
    def __init__(self, model, og_dataset, test=test_diff_f1, threshold=0.1):
        self.dataset = og_dataset
        self.model = model
        self.test = test
        self.threshold = threshold

    def _diff_test(self, data_slice):
        # Convert slice to Giskard Dataframe
        g_dataset = Dataset(
            data_slice,
            target_col=self.dataset.target,
            class_labels=self.dataset.class_labels,
            column_types=self.dataset.column_types,
        )
        # Apply the test
        test_res = self.test(
            actual_slice=g_dataset,
            reference_slice=self.dataset,
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
            logging.debug(f"Mood’s median test signals no significance in the slices, stopping now.")
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
