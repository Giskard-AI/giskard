from typing import Sequence

import matplotlib
import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from ..visualization.widget import get_template
from .knowledge_base import KnowledgeBase
from .question_generators import QUESTION_ATTRIBUTION, QuestionTypes, RAGComponents
from .testset import QATestset


def get_colors(values, cmap_name="RdYlGn"):
    cmap = matplotlib.cm.get_cmap(cmap_name)
    normalizer = matplotlib.colors.Normalize()
    colors = ["#%02x%02x%02x" % (int(r), int(g), int(b)) for r, g, b, _ in 255 * cmap(normalizer(values))]
    return colors


class RAGReport:
    ragas_metrics_names = ["context_precision", "faithfulness", "answer_relevancy", "context_recall"]

    def __init__(
        self,
        results: Sequence[dict],
        testset: QATestset,
        knowledge_base: KnowledgeBase,
        ragas_metrics: pd.DataFrame = None,
    ):
        self._results = results
        self._testset = testset
        self._knowledge_base = knowledge_base

        self._dataframe = testset.to_pandas().copy()
        self._dataframe["evaluation_result"] = [r["evaluation"] for r in results]
        self._dataframe["evaluation_reason"] = [r["reason"] for r in results]
        self._dataframe["assistant_answer"] = [r["assistant_answer"] for r in results]

        if ragas_metrics is not None:
            self._dataframe = pd.concat(
                [self._dataframe, ragas_metrics.set_index("id")[self.ragas_metrics_names]], axis=1
            )

    def _repr_html_(self):
        tpl = get_template("rag_report/rag_report.html")
        kb_script, kb_div = components(self._knowledge_base.plot_topics())
        q_type_script, q_type_div = components(self.plot_correctness_by_metadata("question_type"))
        topic_script, topic_div = components(self.plot_correctness_by_metadata("question_type"))
        return tpl.render(
            knowledge_script=kb_script,
            knowledge_div=kb_div,
            recommendation="Placeholder for the recommmendation.... ",
            components=self.component_scores().to_dict()["score"],
            correctness=self._dataframe["evaluation_result"].mean(),
            q_type_correctness_script=q_type_script,
            q_type_correctness_div=q_type_div,
            topic_correctness_script=topic_script,
            topic_correctness_div=topic_div,
            ragas_metrics={
                "Overall": {
                    "Faithfulness": 0.5,
                    "Answer Relevancy": 0.5,
                    "Context Precision": 0.5,
                    "Context Recall": 0.5,
                },
                "Topics": {
                    "Faithfulness": 0.5,
                    "Answer Relevancy": 0.5,
                    "Context Precision": 0.5,
                    "Context Recall": 0.5,
                },
                "Question": {
                    "Faithfulness": 0.5,
                    "Answer Relevancy": 0.5,
                    "Context Precision": 0.5,
                    "Context Recall": 0.5,
                },
            },
        )

    def save(self, path):
        with open(path, "w") as f:
            f.write(self._repr_html_())

    @property
    def failures(self):
        return self._dataframe[self._dataframe["evaluation_result"] is False]

    def correctness_by_question_type(self):
        correctness = self.correctness_by_metadata("question_type")
        correctness.index = correctness.index.map(lambda x: QuestionTypes(x).name)
        return correctness

    def component_scores(self):
        correctness = self.correctness_by_question_type()
        available_question_types = {
            component: list(set([a.name for a in attribution]).intersection(correctness.index))
            for component, attribution in QUESTION_ATTRIBUTION.items()
        }

        scores = {
            component: [sum(1 / len(attribution) * correctness.loc[q_type, "correctness"] for q_type in attribution)]
            if len(attribution) > 0
            else [np.nan]
            for component, attribution in available_question_types.items()
        }

        score_df = pd.DataFrame.from_dict(scores, orient="index")
        score_df.columns = ["score"]
        score_df.index.rename("RAG Components", inplace=True)
        score_df.index = score_df.index.map(lambda x: RAGComponents(x).name)
        return score_df

    def correctness_by_metadata(self, metadata_name: str):
        correctness = (
            self._dataframe.groupby(lambda idx: self._dataframe.loc[idx, "metadata"][metadata_name])[
                "evaluation_result"
            ]
            .mean()
            .to_frame()
        )
        correctness.columns = ["correctness"]
        correctness.index.rename(metadata_name, inplace=True)
        return correctness

    def plot_correctness_by_metadata(self, metadata_name: str):
        data = self.correctness_by_metadata(metadata_name)
        metadata_values = data.index.tolist()
        metadata_values = [QuestionTypes(v).name for v in metadata_values]
        overall_correctness = self._dataframe["evaluation_result"].mean()
        correctness = (data["correctness"].tolist() - overall_correctness) / overall_correctness * 100

        source = ColumnDataSource(
            data={"correctness": correctness, "metadata_values": metadata_values, "colors": get_colors(correctness)}
        )

        p = figure(
            y_range=metadata_values,
            height=350,
            title=f"Correctness by {metadata_name}",
            toolbar_location=None,
            tools="",
        )

        p.hbar(y="metadata_values", right="correctness", source=source, height=0.9, fill_color="colors")
        p.xaxis.axis_label = "Correctness shift (%) against the overall correctness on the testset"

        return p
