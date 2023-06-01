import numpy as np
import pandas as pd
from sklearn import metrics
from typing import Optional
from collections import defaultdict
from pandas.api.types import is_numeric_dtype, is_categorical_dtype

from giskard.scanner.issue import Issue
from ..models.base import BaseModel
from ..datasets.base import Dataset

from .result import ScanResult
from ..slicing.opt_slicer import OptSlicer
from ..slicing.text_slicer import TextSlicer
from ..slicing.tree_slicer import DecisionTreeSlicer
from ..slicing.category_slicer import CategorySlicer
from ..slicing.multiscale_slicer import MultiscaleSlicer
from ..slicing.bruteforce_slicer import BruteForceSlicer
from ..ml_worker.testing.utils import Direction
from ..ml_worker.testing.tests.performance import (
    test_diff_f1,
    test_diff_rmse,
    test_diff_accuracy,
    test_diff_recall,
    test_diff_precision,
)


class PerformanceScan:
    tags = ["performance", "classification", "regression"]

    def __init__(self, model: Optional[BaseModel] = None, dataset: Optional[Dataset] = None, test_names=None):
        self.params = {}
        self.model = model
        self.dataset = dataset
        self.test_names = test_names

    def run(
        self,
        model: Optional[BaseModel] = None,
        dataset: Optional[Dataset] = None,
        slicer="opt",
        test_names: list = None,
        threshold=-0.1,
    ):
        model = model or self.model
        dataset = dataset or self.dataset
        test_names = test_names or self.test_names
        tests = []

        if test_names is None:
            if model.is_classification:
                tests.append(test_diff_f1)
            else:
                tests.append(test_diff_rmse)
        else:
            for test_name in test_names:
                if test_name == "f1":
                    tests.append(test_diff_f1)
                if test_name == "accuracy":
                    tests.append(test_diff_accuracy)
                if test_name == "recall":
                    tests.append(test_diff_recall)
                if test_name == "precision":
                    tests.append(test_diff_precision)
                if test_name == "rmse":
                    tests.append(test_diff_rmse)

        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        # …

        # Calculate loss
        meta = self._calculate_meta(model, dataset)
        slices = self._find_slices(dataset.select_columns(model.meta.feature_names), model, meta, slicer)

        # Keep only slices of size at least 5% of the dataset
        slices = [s for s in slices if 0.05 * len(dataset) <= len(dataset.slice(s))]

        issues = self._find_issues(slices, model, dataset, meta, tests, threshold)

        return PerformanceScanResult(issues)

    def _find_issues(self, slices, model, dataset, dataset_meta, tests, threshold):
        issues = []
        for s in slices:
            for test in tests:
                test_result = self._diff_test(s, model, dataset, test, threshold)
                if not test_result.passed:
                    issues.append(Issue(s, model, dataset, dataset_meta, test_result, self._get_test_name(test)))

        return issues

    def _get_test_name(self, test):
        # @TODO: throw this away when we can
        if test.meta.name.endswith("f1"):
            return "F1 score"
        if test.meta.name.endswith("accuracy"):
            return "Accuracy"
        if test.meta.name.endswith("recall"):
            return "Recall"
        if test.meta.name.endswith("rmse"):
            return "RMSE"
        if test.meta.name.endswith("precision"):
            return "Precision"

    def _diff_test(self, slice_fn, model, dataset, test_fn, threshold):
        # Apply the test
        test = test_fn(
            actual_dataset=dataset.slice(slice_fn),
            reference_dataset=dataset,  # Could exclude slice_dataset for independence
            model=model,
            threshold=threshold,
            direction=Direction.Increasing,
        )

        res = test.execute()

        return res

    def _calculate_meta(self, model, dataset):
        true_target = dataset.df.loc[:, dataset.target].values
        pred = model.predict(dataset)

        loss_values = [
            metrics.log_loss([true_label], [probs], labels=model.meta.classification_labels)
            for true_label, probs in zip(true_target, pred.raw)
        ]

        return pd.DataFrame({"__gsk__loss": loss_values}, index=dataset.df.index)

    def _find_slices(self, dataset, model, meta: pd.DataFrame, slicer_name):
        df_with_meta = dataset.df.join(meta)
        target_col = "__gsk__loss"

        # @TODO: Handle this properly once we have support for metadata in datasets
        column_types = dataset.column_types.copy()
        column_types["__gsk__loss"] = "numeric"
        dataset_with_meta = Dataset(df_with_meta, target=dataset.target, column_types=column_types)

        # Columns by type
        cols_by_type = {
            type_val: [col for col, col_type in dataset.column_types.items() if col_type == type_val]
            for type_val in ["numeric", "category", "text"]
        }

        # Numerical features
        slicer = self._get_slicer(slicer_name, dataset_with_meta, target_col)

        slices = []
        for col in cols_by_type["numeric"]:
            slices.extend(slicer.find_slices([col]))

        # Categorical features
        slicer = CategorySlicer(dataset_with_meta, target=target_col)
        for col in cols_by_type["category"]:
            slices.extend(slicer.find_slices([col]))

        # @TODO: FIX THIS
        # Text features
        slicer = TextSlicer(dataset_with_meta, target=target_col)
        for col in cols_by_type["text"]:
            slices.extend(slicer.find_slices([col]))

        # @TODO: Should probably bind back to original dataset, but how to to pass
        # cleanly also the metadata needed for the plots? Maybe need a wrapper object
        # like Issue or similar.

        return slices

    def _get_slicer(self, slicer_name, dataset, target):
        if slicer_name == "opt":
            return OptSlicer(dataset, target=target)
        if slicer_name == "tree":
            return DecisionTreeSlicer(dataset, target=target)
        if slicer_name == "ms":
            return MultiscaleSlicer(dataset, target=target)
        if slicer_name == "bf":
            return BruteForceSlicer(dataset, target=target)

        raise ValueError(f"Invalid slicer `{slicer_name}`.")


class PerformanceScanResult(ScanResult):
    def __init__(self, issues):
        self.issues = issues

    def has_issues(self):
        return len(self.issues) > 0

    def __repr__(self):
        if not self.has_issues():
            return "<PerformanceScanResult (no issues)>"

        return f"<PerformanceScanResult ({len(self.issues)} issue{'s' if len(self.issues) > 1 else ''})>"

    def _ipython_display_(self):
        from IPython.core.display import display_html

        html = self._repr_html_()
        display_html(html, raw=True)

    def _repr_html_(self):
        from jinja2 import Environment, PackageLoader, select_autoescape

        env = Environment(
            loader=PackageLoader("giskard.scanner", "templates"),
            autoescape=select_autoescape(),
        )
        tpl = env.get_template("scan_results.html")
        html = tpl.render(
            issues=self.issues,
            num_major_issues=len([i for i in self.issues if i.is_major]),
            num_medium_issues=len([i for i in self.issues if not i.is_major]),
        )

        escaped = html.replace('"', "&quot;")

        return f'''<iframe srcdoc="{escaped}" style="width: 100%; border: none;" class="gsk-scan"></iframe>
<script>
(function() {{
    // @TODO: fix this
    let elements = document.querySelectorAll(".gsk-scan");
    elements.forEach(el => {{
        el.style.height = el.contentWindow.document.body.scrollHeight + "px";
        setTimeout(() => {{
            el.style.height = el.contentWindow.document.body.scrollHeight + "px";
        }}, 1000)

    }})
}})()
</script>
'''

    def to_dataframe(self):
        df = pd.DataFrame(
            [
                {
                    "slice": str(issue.slice_fn),
                    "metric": issue.test_name,
                    "metric_value": f"{issue.test_results.metric*100:.2f}% than global",
                    "size": f"{issue.test_results.actual_slices_size[0]} samples ({100 * (issue.test_results.actual_slices_size[0] / issue.test_results.reference_slices_size[0]):.2f}%)",
                }
                for issue in self.issues
            ]
        )
        return df
