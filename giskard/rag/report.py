from typing import Optional, Sequence, Union

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from giskard.llm.client.base import LLMClient

from ..visualization.widget import get_template
from .knowledge_base import KnowledgeBase
from .question_generators import QUESTION_ATTRIBUTION, QuestionTypes, RAGComponents
from .testset import QATestset


def get_colors(values, cmap_name="RdYlGn"):
    cmap = matplotlib.colormaps[cmap_name]
    normalizer = matplotlib.colors.Normalize()
    colors = ["#%02x%02x%02x" % (int(r), int(g), int(b)) for r, g, b, _ in 255 * cmap(normalizer(values))]
    return colors


class RAGReport:
    """
    Report class for the RAG model evaluation.

    Parameters
    ----------
    results : Sequence[dict]
        The evaluation results of the assistant's answers. Should be a list of dictionaries with the following keys: "evaluation", "reason", "assistant_answer".
    testset : QATestset
        The testset used to evaluate the assistant.
    knowledge_base : KnowledgeBase
        The knowledge base used to create the testset.
    metrics_results : pd.DataFrame, optional
        The additional metrics computed during the evaluation. If provided, these metrics will be included in the report.
    """

    def __init__(
        self,
        testset: QATestset,
        answers: Sequence[str],
        metrics_results: dict,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        self._testset = testset
        self._answers = answers
        self._metrics_results = metrics_results
        self._knowledge_base = knowledge_base

        self._dataframe = testset.to_pandas().copy()
        self._dataframe["assistant_answer"] = answers
        for metric, df in metrics_results.items():
            print(df)
            # if metric == "correctness":
            #     correctness = df["correctness"].apply(lambda x: x["evaluation"])
            #     correctness_reason = df["correctness"].apply(lambda x: x["reason"])
            #     df["correctness"] = correctness
            #     df["correctness_reason"] = correctness_reason

            self._dataframe = self._dataframe.join(df, on="id")
        print(self._dataframe)
        print(self._dataframe.columns)

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
            correctness=self.correctness,
            q_type_correctness_script=q_type_script,
            q_type_correctness_div=q_type_div,
            topic_correctness_script=topic_script,
            topic_correctness_div=topic_div,
            metric_histograms=self.get_metrics_histograms(),
        )

    def save_html(self, path: str):
        """
        Save the report as an HTML file.

        Parameters
        ----------
        path : str or Path
            The path to save the report.
        """

        with open(path, "w", encoding="utf-8") as f:
            f.write(self._repr_html_())

    def save(self, folder_path: str):
        """
        Save all the report data to a folder. This includes the HTML report, the testset, the knowledge base, the evaluation results and the metrics if provided.

        Parameters
        ----------
        folder_path : str or Path
            The folder path to save the report data.
        """
        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)
        self.save_html(path / "report.html")
        self._testset.save(path / "testset.json")

        self._knowledge_base._knowledge_base_df.to_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        with open(path / "knowledge_base_meta.json", "w", encoding="utf-8") as f:
            json.dump(self._knowledge_base.get_savable_data(), f)

        with open(path / "assistant_answer.json", "w", encoding="utf-8") as f:
            json.dump(self._answers, f)

        if self._metrics_results is not None:
            for metric, df in self._metrics_results.items():
                df.reset_index().to_json(path / f"metric_{metric}.jsonl", orient="records", lines=True)

    @classmethod
    def load(cls, folder_path: str, llm_client: LLMClient = None):
        """
        Load a report from a folder. It reconstructs the objects inside the report including the testset and the knowledge base.

        Parameters
        ----------
        folder_path : str or Path
            The folder path to load the report data from.
        llm_client : LLMClient, optional
            The LLMClient to use inside the knowledge base. If not provided, the default client will be used.
        """
        path = Path(folder_path)
        knowledge_base_meta = json.load(open(path / "knowledge_base_meta.json", "r"))
        knowledge_base_data = pd.read_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        testset = QATestset.load(path / "testset.json")

        answers = json.load(open(path / "assistant_answer.json", "r"))

        topics = {int(k): topic for k, topic in knowledge_base_meta.pop("topics", None).items()}
        documents_topics = [int(topic_id) for topic_id in knowledge_base_meta.pop("documents_topics", None)]

        knowledge_base = KnowledgeBase(knowledge_base_data, llm_client=llm_client, **knowledge_base_meta)
        knowledge_base._topics_inst = topics

        if documents_topics is not None:
            for doc_idx, doc in enumerate(knowledge_base._documents):
                doc.topic_id = documents_topics[doc_idx]

        metrics_results = {}
        for file in path.iterdir():
            if file.suffix == ".jsonl" and file.name.startswith("metric_"):
                metric_name = file.name.replace("metric_", "").replace(".jsonl", "")
                metrics_results[metric_name] = pd.read_json(file, orient="records", lines=True)
                metrics_results[metric_name]["id"] = metrics_results[metric_name]["id"].astype(str)
                metrics_results[metric_name].set_index("id", inplace=True)

        return cls(testset, answers, metrics_results, knowledge_base)

    @property
    def failures(self) -> pd.DataFrame:
        return self._dataframe[~self._dataframe["correctness"]]

    def get_failures(
        self,
        topic: Optional[Union[str, Sequence[str]]] = None,
        question_type: Optional[Union[QuestionTypes, Sequence[QuestionTypes]]] = None,
    ) -> pd.DataFrame:
        """
        Retrieves the failures from the results, optionally filtering by topic and question type.

        Parameters
        ----------
        topic : str or Sequence[str], optional
            The topic(s) to filter the failures by.
        question_type : QuestionTypes or Sequence[QuestionTypes], optional
            The question type(s) to filter the failures by.
        """
        failures = self.failures

        if topic:
            topic = [topic] if not isinstance(topic, Sequence) else topic
            failures = failures[failures["metadata"].apply(lambda x: x.get("topic") in topic)]
        if question_type:
            question_type = [question_type] if not isinstance(question_type, Sequence) else question_type
            failures = failures[failures["metadata"].apply(lambda x: x.get("question_type") in question_type)]

        return failures

    @property
    def correctness(self) -> float:
        """
        Compute the overall correctness of the assistant's answers.
        """
        return self._dataframe["correctness"].mean()

    def correctness_by_question_type(self) -> pd.DataFrame:
        """
        Compute the correctness by question type.
        """
        correctness = self._correctness_by_metadata("question_type")
        correctness.index = correctness.index.map(lambda x: QuestionTypes(x).name)
        return correctness

    def correctness_by_topic(self) -> pd.DataFrame:
        """
        Compute the correctness by topic.
        """
        return self._correctness_by_metadata("topic")

    def component_scores(self) -> pd.DataFrame:
        """
        Compute the scores for each RAG component.
        """
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
        """
        Compute the correctness by a metadata field.
        """
        correctness = (
            self._dataframe["correctness"]
            .groupby(lambda idx: self._dataframe.loc[idx, "metadata"][metadata_name])
            .mean()
            .to_frame()
        )

        correctness.index.rename(metadata_name, inplace=True)
        return correctness

    def plot_correctness_by_metadata(self, metadata_name: str):
        """
        Create a bokeh plot showing the correctness by a metadata field.
        """
        data = self._correctness_by_metadata(metadata_name)
        metadata_values = data.index.tolist()
        if metadata_name == "question_type":
            metadata_values = [QuestionTypes(v).name for v in metadata_values]
        overall_correctness = self.correctness
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
            width_policy="max",
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

    def plot_metrics_hist(self, metric_name: str, filter_metadata: dict = None):
        """
        Create a bokeh histogram plot for a RAGAS metric.

        Parameters
        ----------
        metric_name : str
            The name of the RAGAS metric to plot.
        filter_metadata : dict, optional
            Aggregate the question that have the specified metadata values. The keys of the dictionary should be the metadata names and the values should be the metadata values to filter by.
        """
        if metric_name in self._metrics_results:
            if filter_metadata is not None:
                data = self._metrics_results[metric_name][
                    self._dataframe["metadata"].apply(lambda x: all(x.get(k) in v for k, v in filter_metadata.items()))
                ][metric_name]
            else:
                data = self._metrics_results[metric_name]

            p = figure(
                width=300,
                height=200,
                toolbar_location=None,
                title=metric_name.replace("_", " "),
                tools="hover",
                width_policy="max",
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

    def _get_plot_components(self, p):
        script, div = components(p)
        return {"script": script, "div": div}

    def get_metrics_histograms(self):
        histograms_dict = {}
        histograms_dict["Overall"] = {
            "Overall": {
                metric: self._get_plot_components(self.plot_metrics_hist(metric))
                for metric in self._metrics_results
                if metric != "correctness"
            }
        }
        histograms_dict["Topics"] = {
            topic: {
                metric: self._get_plot_components(self.plot_metrics_hist(metric, {"topic": [topic]}))
                for metric in self._metrics_results
                if metric != "correctness"
            }
            for topic in self._testset.get_metadata_values("topic")
        }
        histograms_dict["Question"] = {
            QuestionTypes(q_type).name: {
                metric: self._get_plot_components(self.plot_metrics_hist(metric, {"question_type": [q_type]}))
                for metric in self._metrics_results
                if metric != "correctness"
            }
            for q_type in self._testset.get_metadata_values("question_type")
        }
        return histograms_dict
