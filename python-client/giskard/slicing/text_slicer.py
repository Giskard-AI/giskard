"""
@TODO: This is a hackish implementation of the text slices.
"""
import numpy as np
import pandas as pd
from typing import Optional, Sequence

from giskard.datasets.base import Dataset
from giskard.slicing.category_slicer import CategorySlicer
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction

from .base import BaseSlicer
from .stop_words import sw_en, sw_fr
from .slice import Query, QueryBasedSliceFunction, StringContains
from .utils import get_slicer


class TextSlicer(BaseSlicer):
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
        top_tokens_slices = self.find_top_tokens_slices(feature, target)

        slice_candidates = metadata_slices + top_tokens_slices

        # @TODO: filter slices
        slices = slice_candidates

        return slices

    def find_metadata_slices(self, feature, target):
        slices = []
        data = self.dataset.df

        # @TODO: this is bad, wait for support of metadata in Datasets
        meta = _calculate_text_metadata(data[feature]).add_prefix("__gsk__meta__")
        data_with_meta = data.join(meta)

        # @TODO: hard coded for now, waiting for more organic Database API with meta support
        column_types = self.dataset.column_types.copy()
        column_types["__gsk__meta__charset"] = "category"
        column_types["__gsk__meta__avg_word_length"] = "numeric"
        column_types["__gsk__meta__text_length"] = "numeric"
        dataset_with_meta = Dataset(data_with_meta, target=self.dataset.target, column_types=column_types)

        # Run a slicer for numeric
        slicer = get_slicer(self.slicer, dataset_with_meta, target=target)
        for col in filter(lambda x: column_types[x] == "numeric", meta.columns):
            slices.extend(slicer.find_slices([col]))

        # Run a slicer for categorical
        slicer = CategorySlicer(dataset_with_meta, target=target)
        for col in filter(lambda x: column_types[x] == "category", meta.columns):
            slices.extend(slicer.find_slices([col]))

        # @TODO: previous code will create non-working slices, since those are query-based but
        # the queries will act on a different dataset, so we need to encapsulate this into a
        # special slice function that will recalculate everytime the text properties.
        slices = [TextMetadataSliceFunction(s.query, feature) for s in slices]

        return slices

    def find_top_tokens_slices(self, feature, target):
        slices = []

        tokens = self._get_top_tokens(self.dataset.df[feature])

        for token in tokens:
            slices.append(QueryBasedSliceFunction(Query([StringContains(feature, token)])))

        return slices

    def _get_top_tokens(self, feature_data, n=30):
        from sklearn.feature_extraction.text import TfidfVectorizer

        raw_stopwords = sw_en + sw_fr

        tokenizer = TfidfVectorizer().build_tokenizer()
        tokenized_stopwords = sum([tokenizer(stop_word) for stop_word in raw_stopwords], [])

        text_data = feature_data.values.astype("U")
        vectorizer = TfidfVectorizer(stop_words=tokenized_stopwords)
        tfidf = vectorizer.fit_transform(text_data)

        vocab = vectorizer.vocabulary_
        inv_vocab = {v: k for k, v in vocab.items()}

        # Compute the global TF-IDF score for each word.
        global_tfidf = np.asarray(tfidf.mean(axis=0)).squeeze()
        sorted_global_tfidf_indices = global_tfidf.argsort()[::-1]

        # Get the top n words sorted by global TF-IDF score.
        top_words = [inv_vocab[sorted_global_tfidf_indices[i]] for i in range(n)]

        return top_words


def _calculate_text_metadata(feature_data: pd.Series):
    import chardet

    return pd.DataFrame(
        {
            "text_length": feature_data.map(len),
            "avg_word_length": feature_data.map(_avg_word_length),
            "charset": pd.Categorical(feature_data.map(lambda x: chardet.detect(x.encode())["encoding"])),
        },
        index=feature_data.index,
    )


def _avg_word_length(text):
    words = text.split()
    if len(words) == 0:
        return 0.0
    return np.mean([len(w) for w in words])



# @TODO: this is a temporary hack, will be removed once we have a proper way to handle metadata
class TextMetadataSliceFunction(SlicingFunction):
    row_level = False

    def __init__(self, query: Query, feature: str):
        self.query = query
        self.feature = feature

    def __call__(self, data: pd.DataFrame):
        # @TODO: this is the slowest part, should disappear once we support metadata
        meta = _calculate_text_metadata(data[self.feature]).add_prefix("__gsk__meta__")

        data_with_meta = data.join(meta)
        data_filtered = self.query.run(data_with_meta)
        
        # @TODO: HACK HACK HACK we do this just to avoid returning an empty slice
        # It will get filtered out later, but we need to return something.
        if len(data_filtered) == 0:
            return data_with_meta.loc[:, data.columns].iloc[:1]

        return data_filtered.loc[:, data.columns]

    def __str__(self):
        # @TODO: hard coded for now!
        col = list(self.query.clauses.keys())[0].removeprefix("__gsk__meta__")
        return self.query.to_pandas().replace(f"__gsk__meta__{col}", f"{col}({self.feature})")
