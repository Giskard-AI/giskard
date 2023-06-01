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

from giskard.ml_worker.testing.tests.performance import test_diff_f1, test_diff_rmse, test_diff_accuracy, \
    test_diff_recall, test_diff_precision


class PerformanceScan:
    tags = ["performance", "classification", "regression"]

    def __init__(self, model: Optional[BaseModel] = None, dataset: Optional[Dataset] = None, test_names=None):
        self.params = {}
        self.model = model
        self.dataset = dataset
        self.test_names = test_names

    def run(self, model: Optional[BaseModel] = None, dataset: Optional[Dataset] = None, slicer="opt", test_names=None,
            threshold=0.1):
        model = model or self.model
        dataset = dataset or self.dataset
        test_names = test_names or self.test_names

        if test_names == "f1":
            test = test_diff_f1
        if test_names == "accuracy":
            test = test_diff_accuracy
        if test_names == "recall":
            test = test_diff_recall
        if test_names == "precision":
            test = test_diff_precision
        if test_names == "rmse":
            test = test_diff_rmse
        if test_names is None:
            if model.is_classification:
                test = test_diff_f1
            else:
                test = test_diff_rmse

        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        # …

        # Calculate loss
        meta = self._calculate_meta(model, dataset)
        slices = self.find_slices(dataset.select_columns(model.meta.feature_names), meta, slicer)
        issues = self._find_issues(slices, model, dataset, test, threshold)

        return PerformanceScanResult(issues)

    def _find_issues(self, slices, model, dataset, test, threshold):
        issues = []
        for s in slices:
            actual_slices_size, reference_slices_size, metric, passed = self._diff_test(s, test, threshold)
            if not passed:
                issues.append(Issue(s, metric, actual_slices_size, reference_slices_size, model, dataset))

        return issues

    def _diff_test(self, data_slice, test, threshold):
        # Convert slice to Giskard Dataframe
        slice_dataset = Dataset(data_slice.data)
        # target_col=self.dataset.target,
        # column_types=self.dataset.column_types

        # Apply the test
        test_res = test(
            actual_slice=slice_dataset,
            reference_slice=self.dataset,  # Could exclude slice_dataset for independence
            model=self.model,
            threshold=threshold,
        )

        return test_res

    def _calculate_meta(self, model, dataset):
        true_target = dataset.df.loc[:, dataset.target].values
        pred = model.predict(dataset)

        loss_values = [
            metrics.log_loss([true_label], [probs], labels=model.meta.classification_labels)
            for true_label, probs in zip(true_target, pred.raw)
        ]

        return pd.DataFrame({"__gsk__loss": loss_values}, index=dataset.df.index)

    def find_slices(self, dataset, model, meta: pd.DataFrame, slicer_name):
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
        slicer = CategorySlicer(df_with_meta, target=target_col)
        for col in cols_by_type["category"]:
            slices.extend(slicer.find_slices([col]))

        # @TODO: FIX THIS
        # Text features
        slicer = TextSlicer(df_with_meta, target=target_col)
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

    def _repr_html_(self):
        from collections import defaultdict

        html_output = "<h2>Performance issues</h2>"

        if not self.has_issues():
            html_output += "<p>No issues detected.</p>"
            return html_output

        # Group issues by feature
        grouped_issues = defaultdict(list)
        for s in self.issues:
            grouped_issues[tuple(s.columns())].append(s)

        num_issues = len(grouped_issues)
        html_output += f"<p style='color:#b91c1c;font-size:1.2rem;'>{num_issues} issue{'s' if num_issues > 1 else ''} detected.</p>"

        # Now we render the results for each feature
        for (feature,), issues in grouped_issues.items():
            html_output += "<div style='display:flex'>"
            html_output += "<div style='width:50%'>"
            html_output += f"<h4>Higher than average loss for some values of <code>{feature}</code></h4>"
            html_output += "<ul>"
            for s in issues:
                html_output += "<li><code>" + s.query.to_pandas() + "</code></li>"
            html_output += "</ul>"

            chart_html = self._make_chart_html(feature, issues)
            html_output += "<div style='width:48%;margin-left:2%;'>" + chart_html + "</div>"
            html_output += "</div></div>"

        return html_output

    def _make_chart_html(self, feature, issues):
        import altair as alt
        from altair import Chart

        data = issues[0].data_unsliced.copy()

        pdata = pd.DataFrame(
            {
                "feature": data.loc[:, feature],
                "loss": data.loc[:, "__gsk__loss"],
                "slice": "Background",
                "slice_color": "#1d4ed8",
            }
        )

        if is_numeric_dtype(data[feature].dtype):
            for s in issues:
                s.bind(data)
                f_min, f_max = s.get_column_interval(feature)
                if f_min is None:
                    f_min = pdata.feature.min()
                if f_max is None:
                    f_max = pdata.feature.max()
                pdata.loc[s.mask, "slice"] = f"({f_min:.2f}, {f_max:.2f})"
                pdata.loc[s.mask, "slice_color"] = "#b91c1c"

            base = (
                Chart(pdata)
                .mark_point()
                .encode(
                    x=alt.X("feature:Q", bin=alt.Bin(maxbins=200), title=feature),
                    y=alt.Y(
                        "mean(loss):Q",
                        impute=alt.ImputeParams(value=None),
                        title="Cross-Entropy Loss",
                    ),
                    color=alt.Color("slice_color", scale=None),
                )
            )
            ci = (
                Chart(pdata)
                .mark_errorbar()
                .encode(
                    x=alt.X("feature:Q", bin=alt.Bin(maxbins=200), title=feature),
                    y=alt.Y(
                        "mean(loss):Q",
                        impute=alt.ImputeParams(value=None),
                        title="Cross-Entropy Loss",
                    ),
                    color=alt.Color("slice_color", scale=None),
                )
            )

            h = (
                alt.Chart()
                .mark_rule(strokeDash=[5, 5], strokeWidth=1, color="#1d4ed8")
                .encode(y=alt.datum(pdata[pdata.slice == "Background"].loss.mean()))
            )

            box = (
                alt.Chart(pdata)
                .mark_boxplot(extent="min-max")
                .encode(
                    x=alt.X("slice", title=feature),
                    y=alt.Y("loss", title="Cross-Entropy Loss"),
                )
            )
            chart = (base + ci + h) | box

        if is_categorical_dtype(data[feature].dtype):
            for s in issues:
                s.bind(data)
                pdata.loc[s.mask, "slice"] = s.query.clauses[feature][0].value
                pdata.loc[s.mask, "slice_color"] = "#b91c1c"

            chart = (
                alt.Chart(pdata)
                .mark_boxplot(extent="min-max")
                .encode(
                    x=alt.X("feature", title=feature),
                    y=alt.Y("loss", title="Cross-Entropy Loss"),
                    color=alt.Color("slice_color", scale=None),
                )
            )

        chart_html = chart._repr_mimebundle_()["text/html"]

        return chart_html
