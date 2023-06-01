import numpy as np
import pandas as pd

from .base import BaseSlicer
from .opt_slicer import OptSlicer
from .slice import DataSlice, Query, StringContains


class TextSlicer(BaseSlicer):
    def find_slices(self, features, target=None):
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError(
                "Only single-feature slicing is implemented for now."
            )
        (feature,) = features

        # Make metadata slices
        metadata_slices = self.find_metadata_slices(feature, target)

        # Make top token slices
        top_tokens_slices = self.find_top_tokens_slices(feature, target)

        slice_candidates = metadata_slices + top_tokens_slices

        # @TODO: filter slices
        slices = slice_candidates

        for s in slices:
            s.bind(self.data)

        return slices

    def find_metadata_slices(self, feature, target):
        slices = []

        meta = self._calculate_text_metadata(self.data[feature], prefix=f"{feature}__")
        self.data = self.data.join(meta)

        slicer = OptSlicer(self.data, target=target)
        for col in meta.columns:
            slices.extend(slicer.find_slices([col]))

        return slices

    def find_top_tokens_slices(self, feature, target):
        slices = []

        tokens = self._get_top_tokens(self.data[feature])

        for token in tokens:
            slices.append(DataSlice(Query([StringContains(feature, token)]), self.data))

        return slices

    def _calculate_text_metadata(self, feature_data, prefix=""):
        import chardet

        return pd.DataFrame(
            {
                f"{prefix}text_length": feature_data.map(len),
                f"{prefix}avg_word_length": feature_data.map(
                    lambda x: np.mean([len(w) for w in x.split()])
                ),
                f"{prefix}charset": pd.Categorical(
                    feature_data.map(lambda x: chardet.detect(x.encode())["encoding"])
                ),
            },
            index=feature_data.index,
        )

    def _get_top_tokens(self, feature_data, n=30):
        from sklearn.feature_extraction.text import TfidfVectorizer

        text_data = feature_data.values.astype("U")
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(text_data)

        vocab = vectorizer.vocabulary_
        inv_vocab = {v: k for k, v in vocab.items()}

        # Compute the global TF-IDF score for each word.
        global_tfidf = np.asarray(tfidf.mean(axis=0)).squeeze()
        sorted_global_tfidf_indices = global_tfidf.argsort()[::-1]

        # Get the top n words sorted by global TF-IDF score.
        top_words = [inv_vocab[sorted_global_tfidf_indices[i]] for i in range(n)]

        return top_words
