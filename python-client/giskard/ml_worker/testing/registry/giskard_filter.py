from typing import Callable

import pandas

from giskard.ml_worker.core.savable import Savable


class Filter(Savable):
    filter_func = Callable[[pandas.Series], pandas.Series]

    def __init__(self, filter_func: Callable[[pandas.Series], pandas.Series]):
        self.filter_func = filter_func

    # TODO: implement Savable
    def apply(self, df: pandas.DataFrame) -> pandas.DataFrame:
        return df.filter(lambda row: self.filter_func(row))
