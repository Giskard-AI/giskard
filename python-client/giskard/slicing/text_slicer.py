"""
@TODO: This is a hackish implementation of the text slices.
"""
import logging
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
from ..client.python_utils import warning


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
        token_slices = self.find_token_based_slices(feature, target)

        return metadata_slices + token_slices

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
        column_types["__gsk__meta__avg_whitespace"] = "numeric"
        column_types["__gsk__meta__avg_digits"] = "numeric"
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

    def find_token_based_slices(self, feature, target):
        tokens = set(
            self._get_high_loss_tokens(feature, target)
            + self._get_deviant_tokens(feature, target)
            + self._get_top_tokens(feature, target)
        )

        return [QueryBasedSliceFunction(Query([StringContains(feature, token)])) for token in tokens]

    def _get_top_tokens(self, feature, target, max_tokens=1000):
        from sklearn.feature_extraction.text import TfidfVectorizer

        feature_data = self.dataset.df[feature]
        raw_stopwords = sw_en + sw_fr

        try:
            tokenizer = TfidfVectorizer().build_tokenizer()
            tokenized_stopwords = sum([tokenizer(stop_word) for stop_word in raw_stopwords], [])

            text_data = feature_data.values.astype("U")
            vectorizer = TfidfVectorizer(stop_words=tokenized_stopwords)
            tfidf = vectorizer.fit_transform(text_data)
        except ValueError:
            # Could not get meaningful tokens (e.g. all stop words)
            warning(f"Could not get meaningful tokens for textual feature {feature}. Are you sure this is text?")
            return []

        order = np.argsort(tfidf.max(axis=0).toarray().squeeze())[::-1]
        top_words = vectorizer.get_feature_names_out()[order[:max_tokens]]

        return list(top_words)

    def _get_high_loss_tokens(self, feature, target, max_tokens=1000):
        from scipy import stats
        from sklearn.feature_extraction.text import TfidfVectorizer

        feature_data = self.dataset.df[feature]
        raw_stopwords = sw_en + sw_fr

        try:
            tokenizer = TfidfVectorizer().build_tokenizer()
            tokenized_stopwords = sum([tokenizer(stop_word) for stop_word in raw_stopwords], [])

            text_data = feature_data.values.astype("U")
            vectorizer = TfidfVectorizer(stop_words=tokenized_stopwords)
            tfidf = vectorizer.fit_transform(text_data)
        except ValueError:
            # Could not get meaningful tokens (e.g. all stop words)
            warning(f"Could not get meaningful tokens for textual feature {feature}. Are you sure this is text?")
            return []

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

        tokens = list(vectorizer.get_feature_names_out()[token_idx])
        logging.debug(f"TextSlicer: high loss tokens for {feature} = {tokens}")
        return tokens

    def _get_deviant_tokens(self, feature, target, max_tokens=100):
        from scipy import stats
        from sklearn.feature_extraction.text import CountVectorizer

        critical_target = self.dataset.df[target].quantile(0.75)
        bad_mask = self.dataset.df[target] > critical_target

        test_data = self.dataset.df.loc[bad_mask, feature]
        ref_data = self.dataset.df.loc[~bad_mask, feature]

        try:
            raw_stopwords = sw_en + sw_fr

            tokenizer = CountVectorizer().build_tokenizer()
            tokenized_stopwords = sum([tokenizer(stop_word) for stop_word in raw_stopwords], [])
            vectorizer = CountVectorizer(stop_words=tokenized_stopwords)
            vectorizer.fit(self.dataset.df[feature])
        except ValueError:
            # Could not get meaningful tokens (e.g. all stop words)
            warning(f"Could not get meaningful tokens for textual feature {feature}. Are you sure this is text?")
            return []

        ref_bow = vectorizer.transform(ref_data)
        test_bow = vectorizer.transform(test_data)

        ref_counts = np.asarray(ref_bow.sum(axis=0)).squeeze()
        test_counts = np.asarray(test_bow.sum(axis=0)).squeeze()

        tokens = vectorizer.get_feature_names_out()

        _data = []
        for token, rc, tc in zip(tokens, ref_counts, test_counts):
            stat, pvalue, *_ = stats.chi2_contingency([[rc, tc], [len(ref_data), len(test_data)]])
            if pvalue < 1e-3:
                _data.append({"statistic": stat, "p_value": pvalue, "token": token})

        df = pd.DataFrame(_data, columns=["statistic", "p_value", "token"])
        tokens = df.sort_values("statistic").head(max_tokens).token.tolist()

        return tokens


def _calculate_text_metadata(feature_data: pd.Series):
    import chardet

    # Ensure this is text encoded as a string
    feature_data = feature_data.astype(str)

    return pd.DataFrame(
        {
            "text_length": feature_data.map(len),
            "avg_word_length": feature_data.map(_avg_word_length),
            "charset": pd.Categorical(feature_data.map(lambda x: chardet.detect(x.encode())["encoding"])),
            "avg_whitespace": feature_data.map(_avg_whitespace),
            "avg_digits": feature_data.map(_avg_digits),
        },
        index=feature_data.index,
    )


def _avg_whitespace(text: str):
    chars = list(text)
    if len(chars) == 0:
        return 0.0
    return np.mean([c.isspace() for c in chars])


def _avg_digits(text: str):
    chars = list(text)
    if len(chars) == 0:
        return 0.0
    return np.mean([c.isdigit() for c in chars])


def _avg_word_length(text: str):
    words = text.split()
    if len(words) == 0:
        return 0.0
    return np.mean([len(w) for w in words])


_metadata_cache = {}


# @TODO: this is a temporary hack, will be removed once we have a proper way to handle metadata
class TextMetadataSliceFunction(SlicingFunction):
    row_level = False

    def __init__(self, query: Query, feature: str):
        self.query = query
        self.feature = feature

    def execute(self, data: pd.DataFrame):
        # @TODO: this is the slowest part, should disappear once we support metadata
        import hashlib

        data_id = hashlib.sha256(pd.util.hash_pandas_object(data).values).hexdigest()

        if data_id not in _metadata_cache:
            _metadata_cache[data_id] = _calculate_text_metadata(data[self.feature]).add_prefix("__gsk__meta__")

        meta = _metadata_cache[data_id]
        data_with_meta = data.join(meta)
        data_filtered = self.query.run(data_with_meta)

        return data_filtered.loc[:, data.columns]

    def __str__(self):
        # @TODO: hard coded for now!
        col = list(self.query.clauses.keys())[0].removeprefix("__gsk__meta__")
        return self.query.to_pandas().replace(f"__gsk__meta__{col}", f"{col}({self.feature})")
