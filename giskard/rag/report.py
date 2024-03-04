from typing import Optional, Sequence, Union

import json
from pathlib import Path

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
    ragas_metrics_names = {
        "context_precision": "Context Precision",
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer Relevancy",
        "context_recall": "Context Recall",
    }

    def __init__(
        self,
        results: Sequence[dict],
        testset: QATestset,
        knowledge_base: KnowledgeBase,
        ragas_metrics: pd.DataFrame = None,
    ):
        self._results = results
        self._testset = testset
        self._ragas_metrics = ragas_metrics
        self._knowledge_base = knowledge_base

        self._dataframe = testset.to_pandas().copy()
        self._dataframe["evaluation_result"] = [r["evaluation"] for r in results]
        self._dataframe["evaluation_reason"] = [r["reason"] for r in results]
        self._dataframe["assistant_answer"] = [r["assistant_answer"] for r in results]

        if ragas_metrics is not None:
            self._dataframe = pd.concat(
                [self._dataframe, ragas_metrics.set_index("id")[self.ragas_metrics_names.keys()]], axis=1
            )

    def _repr_html_(self):
        tpl = get_template("rag_report/rag_report.html")
        kb_script, kb_div = components(self._knowledge_base.plot_topics())
        q_type_script, q_type_div = components(self.plot_correctness_by_metadata("question_type"))
        topic_script, topic_div = components(self.plot_correctness_by_metadata("topic"))
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
            ragas_metrics=self.get_ragas_histograms(),
        )

    def save_html(self, path):
        with open(path, "w") as f:
            f.write(self._repr_html_())

    def save(self, folder_path):
        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)
        self.save_html(path / "report.html")
        self._testset.save(path / "testset.json")
        self._knowledge_base._knowledge_base_df.to_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        with open(path / "knowledge_base_meta.json", "w") as f:
            json.dump(self._knowledge_base.get_savable_data(), f)
        with open(path / "eval_results.json", "w") as f:
            json.dump(self._results, f)

        if self._ragas_metrics is not None:
            self._ragas_metrics.to_json(path / "ragas_metrics.jsonl", orient="records", lines=True)

    @classmethod
    def load(cls, folder_path, llm_client=None):
        path = Path(folder_path)
        knowledge_base_meta = json.load(open(path / "knowledge_base_meta.json", "r"))
        knowledge_base_data = pd.read_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        results = json.load(open(path / "eval_results.json", "r"))
        testset = QATestset.load(path / "testset.json")

        topics = {int(k): topic for k, topic in knowledge_base_meta.pop("topics", None).items()}
        documents_topics = [int(topic_id) for topic_id in knowledge_base_meta.pop("documents_topics", None)]

        knowledge_base = KnowledgeBase(knowledge_base_data, llm_client=llm_client, **knowledge_base_meta)
        knowledge_base._topics_inst = topics

        if documents_topics is not None:
            for doc_idx, doc in enumerate(knowledge_base._documents):
                doc.topic_id = documents_topics[doc_idx]

        ragas_metrics = None
        if (path / "ragas_metrics.jsonl").exists():
            ragas_metrics = pd.read_json(path / "ragas_metrics.jsonl", orient="records", lines=True)

        return cls(results, testset, knowledge_base, ragas_metrics)

    @property
    def failures(self):
        return self._dataframe[~self._dataframe["evaluation_result"]]

    def get_failures(
        self,
        topic: Optional[Union[str, Sequence[str]]] = None,
        question_type: Optional[Union[QuestionTypes, Sequence[QuestionTypes]]] = None,
    ):
        failures = self.failures

        if topic:
            topic = [topic] if not isinstance(topic, Sequence) else topic
            failures = failures[failures["metadata"].apply(lambda x: x.get("topic") in topic)]
        if question_type:
            question_type = [question_type] if not isinstance(question_type, Sequence) else question_type
            failures = failures[failures["metadata"].apply(lambda x: x.get("question_type") in question_type)]

        return failures

    def correctness_by_question_type(self):
        correctness = self._correctness_by_metadata("question_type")
        correctness.index = correctness.index.map(lambda x: QuestionTypes(x).name)
        return correctness

    def correctness_by_topic(self):
        return self._correctness_by_metadata("topic")

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

    def _correctness_by_metadata(self, metadata_name: str):
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
        data = self._correctness_by_metadata(metadata_name)
        metadata_values = data.index.tolist()
        if metadata_name == "question_type":
            metadata_values = [QuestionTypes(v).name for v in metadata_values]
        overall_correctness = self._dataframe["evaluation_result"].mean()
        correctness = data["correctness"].to_numpy()
        shift = (data["correctness"].to_numpy() - overall_correctness) / overall_correctness * 100

        source = ColumnDataSource(
            data={
                "correctness_shift": shift,
                "correctness": correctness,
                "metadata_values": metadata_values,
                "colors": get_colors(correctness),
            }
        )

        p = figure(
            y_range=metadata_values,
            height=350,
            title=f"Correctness by {metadata_name}",
            toolbar_location=None,
            tools="hover",
        )

        p.hbar(y="metadata_values", right="correctness_shift", source=source, height=0.9, fill_color="colors")
        p.xaxis.axis_label = "Correctness shift (%) against the overall correctness on the testset"
        p.title.text_font_size = "14pt"
        p.hover.tooltips = [
            (metadata_name, "@metadata_values"),
            ("Correctness", "@correctness{0.00}"),
            ("Correctness shift", "@correctness_shift{0.00}%"),
        ]

        return p

    def plot_ragas_metrics_hist(self, metric_name: str, filter_metadata: dict = None):
        if metric_name in self._dataframe:
            if filter_metadata is not None:
                data = self._dataframe[
                    self._dataframe["metadata"].apply(lambda x: all(x.get(k) in v for k, v in filter_metadata.items()))
                ][metric_name]
            else:
                data = self._dataframe[metric_name]

            p = figure(
                width=300, height=200, toolbar_location=None, title=self.ragas_metrics_names[metric_name], tools="hover"
            )

            bins = np.linspace(0, 1, 21)
            hist, edges = np.histogram(data, bins=bins)
            p.quad(
                top=hist,
                bottom=0,
                left=edges[:-1],
                right=edges[1:],
                fill_color="skyblue",
                line_color="white",
            )
            p.title.text_font_size = "12pt"
            p.hover.tooltips = [
                ("Range", "@left{0.00} to @right{0.00}"),
                ("# questions", "@top"),
            ]

            return p

    def get_plot_components(self, p):
        script, div = components(p)
        return {"script": script, "div": div}

    def get_ragas_histograms(self):
        histograms_dict = {}
        histograms_dict["Overall"] = {
            "Overall": {
                metric: self.get_plot_components(self.plot_ragas_metrics_hist(metric))
                for metric in self.ragas_metrics_names
            }
        }
        histograms_dict["Topics"] = {
            topic: {
                metric: self.get_plot_components(self.plot_ragas_metrics_hist(metric, {"topic": [topic]}))
                for metric in self.ragas_metrics_names
            }
            for topic in self._testset.get_metadata_values("topic")
        }
        histograms_dict["Question"] = {
            QuestionTypes(q_type).name: {
                metric: self.get_plot_components(self.plot_ragas_metrics_hist(metric, {"question_type": [q_type]}))
                for metric in self.ragas_metrics_names
            }
            for q_type in self._testset.get_metadata_values("question_type")
        }
        return histograms_dict
