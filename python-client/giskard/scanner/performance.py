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
        threshold=0.1,
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
        slices = [s for s in slices if len(dataset.slice(s)) / len(dataset) >= 0.05]

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
        tab_header = f"""
<!-- TAB HEADER -->
<div class="flex items-center items-stretch h-10">
    <div class="flex items-center px-4 dark:fill-white border-b border-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 410 213" height="15">
            <path
                d="M318.78 21.94a59.439 59.439 0 0 1 36.45-12.56v.03c7.09-.1 14.13 1.2 20.71 3.84 6.58 2.64 12.57 6.56 17.62 11.54s9.06 10.91 11.8 17.45a53.44 53.44 0 0 1 0 41.3 53.588 53.588 0 0 1-11.8 17.45c-5.05 4.98-11.04 8.9-17.62 11.54s-13.62 3.95-20.71 3.84l-67.92.16-35.87 49.11-135.24 46.84 40.81-47.24a139.229 139.229 0 0 1-66.06-23.8H45.11L0 101.46h55.73C60.38 44.84 115.97 0 183.59 0c31.71 0 63.58 9.86 87.47 27.04a105.149 105.149 0 0 1 26.65 27.18 59.4 59.4 0 0 1 21.07-32.28zM99.85 46.03l55.4 55.45h21.31l-64.81-64.87c-4.18 2.86-8.15 6.01-11.9 9.42zm57.78-28.45 83.9 83.9h21.29l-86.21-86.22c-6.37.32-12.71 1.1-18.98 2.32zm-92.84 98.94H39.72l11.1 9.82h22.44c-3-3.12-5.83-6.4-8.47-9.82zm134.27 0H84.8l-.03.01c20.8 20.91 51.79 33.67 84.66 34.3l29.63-34.31zm-34.81 63.35 77.79-26.94 26.6-36.39h-49.68l-54.71 63.33zm146.77-78.65h46.2l.05.01c9.98-.55 19.36-4.97 26.14-12.32a38.409 38.409 0 0 0 10.16-27.05 38.44 38.44 0 0 0-11.56-26.48 38.405 38.405 0 0 0-26.74-10.94A44.287 44.287 0 0 0 324 37.41a44.268 44.268 0 0 0-12.97 31.28v32.53zm51.82-52.83c5.27.52 9.12 5.22 8.6 10.49-.52 5.27-5.22 9.12-10.49 8.6s-9.12-5.22-8.6-10.49c.53-5.27 5.22-9.12 10.49-8.6z"
                style="fill-rule:evenodd;clip-rule:evenodd" />
        </svg>
        <div class="ml-4 py-2">
            <span class="uppercase text-sm">{len(self.issues)} issues detected</span>
        </div>
    </div>

    <div class="bg-zinc-800 px-3 py-2 border-r border-t border-l border-gray-500">
        Model bias
        <span class="ml-1 rounded-full text-xs min-w-4 min-h-4 px-1 py-0.5 inline-block text-center bg-red-400">{len(self.issues)}</span>
    </div>

    <div class="flex-grow border-b border-gray-500"></div>
</div>
<!-- TAB HEADER END -->
"""
        issues_table = self._make_issues_table_html()

        main_content = f"""
<div class="dark:text-white dark:bg-zinc-800 p-4 pt-4 mb-4">
    <div class="p-3 mt-2 bg-amber-100/40 rounded-sm w-full flex align-middle">
        <div class="text-amber-100">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="mt-0.5 w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
        </div>

        <p class="ml-2 my-1 text-amber-100 text-sm">
            We detected some spots in your data where the model has a tendency to make incorrect
            predictions.
        </p>
    </div>

    <div class="flex items-center space-x-1">
        <h2 class="uppercase my-4 mr-2 font-medium">Issues</h2>
    </div>

    {issues_table}    
    
    <h2 class="uppercase mb-2 mt-8 mr-2 font-mediums flex">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
            stroke="currentColor" class="w-5 h-5 mr-1">
            <path stroke-linecap="round" stroke-linejoin="round"
                d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
        </svg>
        Why does this happen?
    </h2>
    <p class="my-1">
        Performance bias can happen for a different reasons:
    </p>
    <ul class="list-disc ml-6">
        <li>Not enough training samples in the low-performing data slices</li>
        <li>Wrong labels in the training set in the low-performing data slices</li>
        <li>Drift between your training set and the test set</li>
    </ul>

    <h2 class="uppercase mb-2 mt-8 mr-2 font-mediums flex">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
            stroke="currentColor" class="w-5 h-5 mr-1">
            <path stroke-linecap="round" stroke-linejoin="round"
                d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z" />
        </svg>
        How to correct this?
    </h2>
    <p class="my-1 max-w-xl">
        We strongly recommend that you inspect the incorrect samples in the detected low-performing data
        slices. This will allow you to find the right feature engineering or data augmentation strategies to
        avoid such biases.
    </p>

    <div class="my-5 space-x-2">
        <a href="#" class="bg-orange-700 hover:bg-orange-600 inline-block py-2 px-3 rounded-sm">Customize
            Test
            Suite</a>
        <a href="#" class="bg-zinc-500 hover:bg-emerald-500 inline-block py-2 px-3 rounded-sm">Debug Test
            Suite</a>
    </div>
</div>
"""

        html = f"""
<!doctype html>
<html lang="en">
<head>
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {{
    darkMode: 'class'
}}
</script>
<style>
table.dataframe {{
    width: 100%;
    max-width: 100%;
    overflow: auto;
}}
.dataframe tr {{
    border-bottom: 1px solid #555;
}}
.dataframe td, .dataframe th {{
    padding: 0.5rem;
}}
</style>
</head>
<body>
<div class="dark">
<div id="gsk-scan" class="dark:text-white dark:bg-zinc-900">
{tab_header}
{main_content}
</div>
</div>
<script type="text/javascript">
(function() {{
        console.log("Loading Giskard Scan");
        let rows = document.querySelectorAll("#gsk-scan .gsk-issue")
        rows.forEach(rowEl => {{
            rowEl.addEventListener("click", (event) => {{
                event.preventDefault()
                if (event.target.classList.contains("gsk-debug")) {{
                    alert("Not implemented yet")
                    return;
                }}

                rowEl.classList.toggle("open")
                rowEl.classList.toggle("bg-zinc-700")
            }})
        }});
}})()
</script>
</body>
</html>
"""
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

    def _make_issues_table_html(self):
        rows = ""
        for issue in self.issues:
            tr = issue.test_results
            rows += f"""
<tbody class="first:border-t border-b border-zinc-400">
    <tr class="gsk-issue text-sm group peer text-left cursor-pointer hover:bg-zinc-700">
        <td class="p-3">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                stroke-width="1.5" stroke="currentColor" class="w-4 h-4 group-[.open]:rotate-90">
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
        </td>
        <td class="p-3">
            <code class="mono text-blue-300">
                {str(issue.slice_fn).replace("&", "<br>")}
            </code>
        </td>
        <td class="p-3">
            {issue.test_name}
        </td>
        <td class="p-3">
            <span class="{'text-red-400' if issue.is_major else 'text-amber-200'}">{tr.metric*100:.2f}% than global</span>
        </td>
        <td class="p-3">
            <span class="text-gray-400">
                {tr.actual_slices_size[0]} samples ({100 * (tr.actual_slices_size[0] / tr.reference_slices_size[0]):.2f}%)
            </span>
        </td>
        <td class="p-3 text-xs text-right space-x-1">
            <a href=""
                class="gsk-debug inline-block border border-emerald-100/50 text-emerald-100/90 hover:bg-emerald-500 hover:border-emerald-500 hover:text-white px-2 py-0.5 rounded-sm">Debug</a>
        </td>
    </tr>
    <tr class="gsk-issue-detail text-left collapse peer-[.open]:visible border-b border-zinc-400 bg-zinc-700">
        <td colspan="6" class="p-3">
            <h4 class="uppercase">Examples</h4>
            <div class="text-white max-w-xl text-sm overflow-scroll" style="max-width: 920px">
                {issue.examples(3).to_html()}
            </div>
        </td>
    </tr>
</tbody>
"""

        return f"""
<!-- ISSUES TABLE -->
<div class="mb-4">
    <table class="table-auto w-full text-white">
    {rows}
    </table>
</div>
<!-- ISSUES TABLE END -->
"""

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
