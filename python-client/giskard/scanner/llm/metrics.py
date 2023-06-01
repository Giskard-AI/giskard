from abc import abstractmethod
from ctypes import Union

import evaluate
from typing import List, Union, Iterable

import pandas as pd


class LlmMetric:
    @abstractmethod
    def __call__(self, predictions: List[str], references: Union[List[List[str]], List[str]]) -> List[float]:
        ...


class RougeScore(LlmMetric):
    @abstractmethod
    def __call__(self, predictions: List[str], references: Union[List[List[str]], List[str]]) -> List[float]:
        ...

    def _rouge_call(self, predictions, references, rouge_types):
        rouge = evaluate.load('rouge')
        results = rouge.compute(predictions=predictions,
                                references=references,
                                rouge_types=rouge_types,
                                use_aggregator=False)
        rouge_list = list(results.values())[0]
        return pd.Series(rouge_list)


class Rouge1(RougeScore):
    def __call__(self, predictions: Iterable[str], references: Union[Iterable[Iterable[str]], Iterable[str]]) -> \
            Iterable[float]:
        return self._rouge_call(predictions, references, ["rouge1"])


class Rouge2(RougeScore):
    def __call__(self, predictions: Iterable[str], references: Union[Iterable[Iterable[str]], Iterable[str]]) -> \
            Iterable[float]:
        return self._rouge_call(predictions, references, ["rouge2"])
