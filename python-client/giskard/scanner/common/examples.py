from typing import Callable, Optional, Union

import numpy as np

from ...slicing.text_slicer import MetadataSliceFunction
from ..issues import Issue


class ExampleExtractor:
    def __init__(self, issue: Issue, filter_fn: Optional[Callable] = None, sorting_fn: Optional[Callable] = None):
        self.issue = issue
        self.filter_fn = filter_fn
        self.sorting_fn = sorting_fn

    def get_examples_dataframe(self, n=3, with_prediction: Union[int, bool] = 1):
        issue = self.issue
        dataset = issue.dataset.slice(issue.slicing_fn) if issue.slicing_fn else issue.dataset

        # Filter if needed
        if self.filter_fn:
            dataset = self.filter_fn(issue, dataset)

        examples = dataset.df.copy()

        # Keep only interesting columns
        cols_to_show = issue.features
        if issue.dataset.target is not None:
            cols_to_show += [issue.dataset.target]
        examples = examples.loc[:, cols_to_show]

        # If metadata slice, add the metadata column
        if isinstance(issue.slicing_fn, MetadataSliceFunction):
            for col in issue.features:
                meta_cols = issue.slicing_fn.query.columns()
                provider = issue.slicing_fn.provider
                for meta_col in meta_cols:
                    meta_vals = issue.dataset.column_meta[col, provider].loc[examples.index, meta_col]
                    examples.insert(
                        loc=examples.columns.get_loc(col) + 1,
                        column=f"{meta_col}({col})",
                        value=meta_vals,
                        allow_duplicates=True,
                    )

        # Add the model prediction
        if with_prediction:
            model_pred = issue.model.predict(dataset)

            if model_pred.probabilities is not None:
                num_labels_to_print = min(len(issue.model.meta.classification_labels), int(with_prediction))
                pred_examples = []
                for ps in model_pred.raw:
                    label_idx = np.argsort(-ps)[:num_labels_to_print]
                    pred_examples.append(
                        "\n".join([f"{issue.model.meta.classification_labels[i]} (p = {ps[i]:.2f})" for i in label_idx])
                    )
            else:
                pred_examples = model_pred.prediction

            predicted_label = "Predicted"
            if issue.dataset.target is not None:
                predicted_label += f" `{issue.dataset.target}`"
            examples[predicted_label] = pred_examples

        n = min(len(examples), n)
        if n > 0:
            if self.sorting_fn:
                return self.sorting_fn(issue, examples).head(n)

            return examples.head(n)

        return examples
