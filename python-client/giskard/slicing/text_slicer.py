import os
import copy
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from ..ml_worker.testing.registry.registry import get_object_uuid

from ..core.core import DatasetProcessFunctionMeta

from .base import BaseSlicer
from .slice import Query, QueryBasedSliceFunction, ContainsWord
from .utils import get_slicer
from ..client.python_utils import warning
from ..datasets.base import Dataset
from ..ml_worker.testing.registry.slicing_function import SlicingFunction
from ..slicing.category_slicer import CategorySlicer


class TextSlicer(BaseSlicer):
    MAX_TOKENS = int(os.getenv("GSK_TEXT_SLICER_MAX_TOKENS", 1000))

    def __init__(
        self,
        dataset: Dataset,
        features: Optional[Sequence[str]] = None,
        target: Optional[str] = None,
        min_deviation: float = 0.05,
        abs_deviation: bool = False,
        slicer="tree",
    ):
        self.dataset = dataset
        self.features = features
        self.target = target
        self.min_deviation = min_deviation
        self.abs_deviation = abs_deviation
        self.slicer = slicer

    def find_slices(self, features, target=None):
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError("Only single-feature slicing is implemented for now.")
        (feature,) = features

        # Make metadata slices
        metadata_slices = self.find_metadata_slices(feature, target)

        # Make top token slices
        token_slices = self.find_token_based_slices(feature, target)

        return metadata_slices + token_slices

    def find_metadata_slices(self, feature, target):
        slices = []
        data = self.dataset.column_meta[feature, "text"].copy()
        data[target] = self.dataset.df[target]

        meta_dataset = Dataset(data, target=target, validation=False)
        column_types = meta_dataset.column_types.copy()
        column_types.pop(target, None)

        # Run a slicer for numeric
        slicer = get_slicer(self.slicer, meta_dataset, target=target)
        for col in filter(lambda x: column_types[x] == "numeric", column_types.keys()):
            slices.extend(slicer.find_slices([col]))

        # Run a slicer for categorical
        slicer = CategorySlicer(meta_dataset, target=target)
        for col in filter(lambda x: column_types[x] == "category", column_types.keys()):
            slices.extend(slicer.find_slices([col]))

        # Convert slices from metadata to original dataset
        slices = [MetadataSliceFunction(s.query, feature, "text") for s in slices]

        return slices

    def find_token_based_slices(self, feature, target):
        target_is_numeric = pd.api.types.is_numeric_dtype(self.dataset.df[target])
        try:
            tokens = self._get_top_tokens(feature, target)

            if target_is_numeric:
                tokens += self._get_high_loss_tokens(feature, target) + self._get_deviant_tokens(feature, target)

            tokens = set(tokens)
        except VectorizerError:
            # Could not get meaningful tokens (e.g. all stop words)
            warning(f"Could not get meaningful tokens for textual feature `{feature}`. Are you sure this is text?")
            return []

        return [QueryBasedSliceFunction(Query([ContainsWord(feature, token)])) for token in tokens]

    def _get_top_tokens(self, feature, target):
        vectorizer = _make_vectorizer(self.dataset.df[feature], tfidf=True)
        tfidf = vectorizer.transform(self.dataset.df[feature])

        # Get top tokens by TF-IDF
        order = np.argsort(tfidf.max(axis=0).toarray().squeeze())[::-1]
        top_tokens = vectorizer.get_feature_names_out()[order[: self.MAX_TOKENS]]

        return list(top_tokens)

    def _get_high_loss_tokens(self, feature, target):
        from scipy import stats

        max_tokens = self.MAX_TOKENS
        vectorizer = _make_vectorizer(self.dataset.df[feature], tfidf=True)
        tfidf = vectorizer.transform(self.dataset.df[feature])

        lrank = self.dataset.df[target].rank(pct=True)

        # If the vocabulary is too large, prefilter top tokens
        # @TODO: check this
        vocab_size = tfidf.shape[1]
        if vocab_size > max_tokens * 10:
            token_ns = np.argpartition(tfidf.max(axis=0).toarray().squeeze(), max_tokens * 10 - 1)[: max_tokens * 10]
        else:
            token_ns = np.arange(vocab_size)

        # Find tokens which are most correlated with loss
        rank_corrs = np.asarray([stats.spearmanr(tfidf[:, n].toarray().squeeze(), lrank)[0] for n in token_ns])
        token_idx = token_ns[rank_corrs.argsort()[:max_tokens]]

        return list(vectorizer.get_feature_names_out()[token_idx])

    def _get_deviant_tokens(self, feature, target):
        from scipy import stats

        vectorizer = _make_vectorizer(self.dataset.df[feature], tfidf=False, binary=True)
        X = vectorizer.transform(self.dataset.df[feature])

        critical_target = self.dataset.df[target].quantile(0.75)
        y = self.dataset.df[target] > critical_target
        Y = np.stack((1 - y, y), axis=1)

        counts = X.T @ Y
        totals = Y.sum(axis=0)
        remainders = counts - totals
        tokens = vectorizer.get_feature_names_out()

        mask = (counts.max(axis=-1) > 5) & (counts.min(axis=-1) > 0) & (remainders.min(axis=-1) > 0)

        _data = []
        for token, token_counts, token_remainders in zip(tokens[mask], counts[mask], remainders[mask]):
            stat, pvalue, *_ = stats.chi2_contingency([token_counts, token_remainders])
            if pvalue < 1e-3:
                _data.append({"statistic": stat, "token": token})

        df = pd.DataFrame(_data, columns=["statistic", "token"])
        tokens = df.sort_values("statistic").head(self.MAX_TOKENS).token.tolist()

        return tokens


class VectorizerError(ValueError):
    """Raised when a vectorizer could not be created (e.g. empty dictionary)."""


def _make_vectorizer(data: pd.Series, tfidf=False, **kwargs):
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from .stop_words import sw_en, sw_fr

    raw_stopwords = sw_en + sw_fr
    vectorizer = TfidfVectorizer(**kwargs) if tfidf else CountVectorizer(**kwargs)
    tokenizer = vectorizer.build_tokenizer()

    tokenized_stopwords = sum([tokenizer(stop_word) for stop_word in raw_stopwords], [])
    vectorizer.set_params(stop_words=tokenized_stopwords)

    try:
        vectorizer.fit(data)
    except ValueError as err:
        raise VectorizerError(str(err)) from err

    return vectorizer


class MetadataSliceFunction(SlicingFunction):
    row_level = False
    needs_dataset = True

    def __init__(self, query: Query, feature: str, provider: str):
        super().__init__(None, row_level=False, cell_level=False)
        self.query = query
        self.feature = feature
        self.provider = provider
        self.meta = DatasetProcessFunctionMeta(type="SLICE")
        self.meta.uuid = get_object_uuid(query)
        self.meta.code = str(self)
        self.meta.name = str(self)
        self.meta.display_name = str(self)
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = "Automatically generated slicing function"

    def execute(self, dataset: Dataset) -> pd.DataFrame:
        metadata = dataset.column_meta[self.feature, self.provider]
        mask = self.query.mask(metadata)

        return dataset.df[mask]

    def __str__(self):
        # Clauses should have format like "avg_word_length(my_column) > x"
        q = copy.deepcopy(self.query)
        for c in q.get_all_clauses():
            c.column += f"({self.feature})"

        return str(q)

    def _should_save_locally(self) -> bool:
        return True
