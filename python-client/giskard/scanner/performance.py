import numpy as np
import pandas as pd
from sklearn import metrics
from pandas.api.types import is_numeric_dtype, is_categorical_dtype


from .result import ScanResult
from ..slicing.opt_slicer import OptSlicer
from ..slicing.text_slicer import TextSlicer
from ..slicing.tree_slicer import DecisionTreeSlicer
from ..slicing.category_slicer import CategorySlicer
from ..slicing.multiscale_slicer import MultiscaleSlicer


class PerformanceScan:
    tags = ["performance", "classification", "regression"]

    def __init__(self, model: None, dataset=None):
        self.params = {}
        self.model = model
        self.dataset = dataset

    def run(self, model=None, dataset=None, slicer="opt"):
        model = model or self.model
        dataset = dataset or self.dataset

        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        # Should check model type
        # …

        # TODO: support giskard.Model
        true_target = dataset.target
        pred = model.predict(self.dataset.to_giskard())

        # Calculate loss
        if "loss" not in dataset.meta().columns:
            loss = np.array(
                [
                    metrics.log_loss([true_label], [probs], labels=dataset.class_labels)
                    for true_label, probs in zip(true_target, pred.raw)
                ]
            )
            dataset.add_meta_column("loss", loss)

        slices = self.find_slices(dataset.select_columns(model.meta.feature_names), slicer)

        return slices

    def find_slices(self, dataset, slicer_name):
        target_col = "meta__loss"

        # Numerical features
        num_cols = list(dataset.select_columns(col_type="number").columns)

        if slicer_name == "opt":
            slicer = OptSlicer(dataset.df(True), target=target_col)
        elif slicer_name == "tree":
            slicer = DecisionTreeSlicer(dataset.df(True), target=target_col)
        elif slicer_name == "ms":
            slicer = MultiscaleSlicer(dataset.df(True), target=target_col)
        else:
            raise ValueError(f"Invalid slicer `{slicer_name}`.")

        slices = []
        for col in num_cols:
            slices.extend(slicer.find_slices([col]))

        # Categorical features
        cat_cols = list(dataset.select_columns(col_type="category").columns)

        slicer = CategorySlicer(dataset.df(True), target=target_col)
        for col in cat_cols:
            slices.extend(slicer.find_slices([col]))

        # @TODO: FIX THIS
        # # Text features
        # text_cols = list(dataset.select_columns(col_type="text").columns)
        # slicer = TextSlicer(dataset.df(True), target=target_col)
        # for col in text_cols:
        #     slices.extend(slicer.find_slices([col]))

        return PerformanceScanResult(slices)


class PerformanceScanResult(ScanResult):
    def __init__(self, slices):
        self.slices = slices

    def has_issues(self):
        return len(self.slices) > 0

    def __repr__(self):
        if not self.has_issues():
            return "<PerformanceScanResult (no issues)>"

        return f"<PerformanceScanResult ({len(self.slices)} issue{'s' if len(self.slices) > 1 else ''})>"

    def _repr_html_(self):
        from collections import defaultdict

        html_output = "<h2>Performance issues</h2>"

        if not self.has_issues():
            html_output += "<p>No issues detected.</p>"
            return html_output

        # Group slices by feature
        grouped_slices = defaultdict(list)
        for s in self.slices:
            grouped_slices[tuple(s.columns())].append(s)

        num_issues = len(grouped_slices)
        html_output += f"<p style='color:#b91c1c;font-size:1.2rem;'>{num_issues} issue{'s' if num_issues > 1 else ''} detected.</p>"

        # Now we render the results for each feature
        for (feature,), slices in grouped_slices.items():
            html_output += "<div style='display:flex'>"
            html_output += "<div style='width:50%'>"
            html_output += f"<h4>Higher than average loss for some values of <code>{feature}</code></h4>"
            html_output += "<ul>"
            for s in slices:
                html_output += "<li><code>" + s.query.to_pandas() + "</code></li>"
            html_output += "</ul>"

            chart_html = self._make_chart_html(feature, slices)
            html_output += (
                "<div style='width:48%;margin-left:2%;'>" + chart_html + "</div>"
            )
            html_output += "</div></div>"

        return html_output

    def _make_chart_html(self, feature, slices):
        import altair as alt
        from altair import Chart

        data = slices[0].data_unsliced.copy()

        pdata = pd.DataFrame(
            {
                "feature": data.loc[:, feature],
                "loss": data.loc[:, "meta__loss"],
                "slice": "Background",
                "slice_color": "#1d4ed8",
            }
        )

        if is_numeric_dtype(data[feature].dtype):
            for s in slices:
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
            for s in slices:
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
