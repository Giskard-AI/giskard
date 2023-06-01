import logging
from scipy import stats


class DataSliceFilter:
    """Selects slices based on their significance."""

    def filter(self, slices):
        raise NotImplementedError()


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
