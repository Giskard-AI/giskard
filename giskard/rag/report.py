from typing import Optional, Sequence, Union

import json
from html import escape
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from IPython.core.display import HTML

from ..llm.client.base import LLMClient
from ..llm.embeddings.base import BaseEmbedding
from ..llm.errors import LLMImportError
from ..visualization.widget import get_template
from .base import AgentAnswer
from .knowledge_base import KnowledgeBase
from .question_generators import COMPONENT_DESCRIPTIONS, QUESTION_ATTRIBUTION, RAGComponents
from .testset import QATestset, QuestionSample

try:
    from bokeh.document import Document
    from bokeh.embed import components
    from bokeh.io import curdoc, output_notebook, reset_output
    from bokeh.models import ColumnDataSource, Span, TabPanel, Tabs
    from bokeh.plotting import figure
except ImportError as err:
    raise LLMImportError(flavor="llm") from err


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
    testset : QATestset
        The testset used to evaluate the agent.
    model_outputs : Sequence[ModelOutput]
        The evaluation results of the agent's answers. Should be a list of dictionaries with the following keys: "evaluation", "reason", "agent_answer".
    metrics_results : dict, optional
        The additional metrics computed during the evaluation. If provided, these metrics will be included in the report. The dict should have the following structure: `{"question_id": {"correctness": bool, "correctness_reason": str, "additional_metric": value, ...}}`.
    knowledge_base : KnowledgeBase
        The knowledge base used to create the testset.
    """

    def __init__(
        self,
        testset: QATestset,
        model_outputs: Sequence[AgentAnswer],
        metrics_results: dict,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        self._testset = testset
        self._model_outputs = model_outputs
        self._metrics_results = metrics_results
        self._knowledge_base = knowledge_base

        self._recommendation = "Placeholder for the recommmendation."

        self._dataframe = testset.to_pandas().copy()
        self._dataframe["agent_answer"] = [answer.message for answer in model_outputs]

        metric_df = pd.DataFrame.from_dict(metrics_results, orient="index")
        self.metric_names = [
            metric for metric in metric_df.columns if metric not in ["correctness", "correctness_reason"]
        ]
        self._dataframe = self._dataframe.join(metric_df, on="id")

    def to_pandas(self):
        return self._dataframe

    def _repr_html_(self, notebook=True):
        if notebook:
            output_notebook()
        else:
            reset_output()

        return self.to_html()

    def to_html(self, filename=None, embed=False):
        """Renders the evaluation report as HTML.

        Saves or returns the HTML representation of the scan report.

        Parameters
        ----------
        filename : Optional[str]
            If provided, the HTML will be written to the file.
        """
        tpl = get_template("rag_report/rag_report.html")

        kb_script, kb_div = (
            components(self._apply_theme(self._get_knowledge_plot())) if self._knowledge_base else (None, None)
        )
        q_type_script, q_type_div = components(
            self._apply_theme(self.plot_correctness_by_metadata("question_type")), theme="dark_minimal"
        )
        topic_script, topic_div = components(
            self._apply_theme(self.plot_correctness_by_metadata("topic")), theme="dark_minimal"
        )

        metric_histograms = self.get_metrics_histograms()

        component_dict = self.component_scores().to_dict()["score"]

        for name, description in COMPONENT_DESCRIPTIONS.items():
            if name in component_dict:
                component_dict[name] = {"score": component_dict[name], "description": description}

        html = tpl.render(
            knowledge_script=kb_script,
            knowledge_div=kb_div,
            recommendation=self._recommendation,
            components=component_dict,
            correctness=self.correctness,
            q_type_correctness_script=q_type_script,
            q_type_correctness_div=q_type_div,
            topic_correctness_script=topic_script,
            topic_correctness_div=topic_div,
            additional_metrics=len(self.metric_names) > 0,
            metric_histograms=metric_histograms,
        )

        if filename is not None:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            return

        if embed:
            return HTML(f'<iframe srcdoc="{escape(html)}" width=100% height=800px></iframe>')
        return html

    def save(self, folder_path: str):
        """Save all the report data to a folder.

        This includes the HTML report, the testset, the knowledge base, the evaluation results and the metrics if
        provided.

        Parameters
        ----------
        folder_path : str or Path
            The folder path to save the report data.
        """
        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)
        self.to_html(path / "report.html")
        self._testset.save(path / "testset.json")

        report_details = {"recommendation": self._recommendation}
        with open(path / "report_details.json", "w", encoding="utf-8") as f:
            json.dump(report_details, f)

        self._knowledge_base._knowledge_base_df.to_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        with open(path / "knowledge_base_meta.json", "w", encoding="utf-8") as f:
            json.dump(self._knowledge_base.get_savable_data(), f)

        with open(path / "agent_answer.json", "w", encoding="utf-8") as f:
            json.dump([{"message": output.message, "documents": output.documents} for output in self._model_outputs], f)

        if self._metrics_results is not None:
            with open(path / "metrics_results.json", "w", encoding="utf-8") as f:
                json.dump(self._metrics_results, f)

    @classmethod
    def load(
        cls, folder_path: str, llm_client: Optional[LLMClient] = None, embedding_model: Optional[BaseEmbedding] = None
    ):
        """Load a saved report.

        It reconstructs the objects inside the report including the testset and the knowledge base.

        Parameters
        ----------
        folder_path : str or Path
            The folder path to load the report data from.
        llm_client : LLMClient, optional
            The LLMClient to use inside the knowledge base. If not provided, the default client will be used.
        embedding_model : BaseEmbedding, optional
            The embedding model to use inside the knowledge base. If not provided, the default model will be used.
        """
        path = Path(folder_path)
        knowledge_base_meta = json.load(open(path / "knowledge_base_meta.json", "r"))
        knowledge_base_data = pd.read_json(path / "knowledge_base.jsonl", orient="records", lines=True)
        testset = QATestset.load(path / "testset.json")

        answers = json.load(open(path / "agent_answer.json", "r"))
        model_outputs = [AgentAnswer(**answer) for answer in answers]

        topics = {int(k): topic for k, topic in knowledge_base_meta.pop("topics", None).items()}
        documents_topics = [int(topic_id) for topic_id in knowledge_base_meta.pop("documents_topics", None)]

        knowledge_base = KnowledgeBase(
            knowledge_base_data,
            llm_client=llm_client,
            embedding_model=embedding_model,
            columns=knowledge_base_meta.pop("columns", None),
            min_topic_size=knowledge_base_meta.pop("min_topic_size", None),
            chunk_size=knowledge_base_meta.pop("chunk_size", None),
            seed=knowledge_base_meta.pop("seed", None),
        )
        knowledge_base._topics_inst = topics

        for doc_idx, doc in enumerate(knowledge_base._documents):
            doc.topic_id = documents_topics[doc_idx]

        metrics_results = {}
        if (path / "metrics_results.json").exists():
            metrics_results = json.load(open(path / "metrics_results.json", "r"))

        report_details = json.load(open(path / "report_details.json", "r"))
        testset._dataframe.index = testset._dataframe.index.astype(str)

        report = cls(testset, model_outputs, metrics_results, knowledge_base)
        report._recommendation = report_details["recommendation"]
        return report

    @property
    def topics(self):
        return self._testset.get_metadata_values("topic")

    @property
    def failures(self) -> pd.DataFrame:
        return self._dataframe[~self._dataframe["correctness"]]

    def get_failures(
        self,
        topic: Optional[Union[str, Sequence[str]]] = None,
        question_type: Optional[Union[str, Sequence[str]]] = None,
    ) -> pd.DataFrame:
        """
        Retrieves the failures from the results, optionally filtering by topic and question type.

        Parameters
        ----------
        topic : str or Sequence[str], optional
            The topic(s) to filter the failures by.
        question_type : str or Sequence[str], optional
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
        Compute the overall correctness of the agent's answers.
        """
        return self._dataframe["correctness"].mean()

    def correctness_by_question_type(self) -> pd.DataFrame:
        """
        Compute the correctness by question type.
        """
        correctness = self._correctness_by_metadata("question_type")
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
            component: list(set([a for a in attribution]).intersection(correctness.index))
            for component, attribution in QUESTION_ATTRIBUTION.items()
        }

        scores = {
            component: (
                [sum(1 / len(attribution) * correctness.loc[q_type, "correctness"] for q_type in attribution)]
                if len(attribution) > 0
                else [1]
            )
            for component, attribution in available_question_types.items()
        }
        scores[RAGComponents.KNOWLEDGE_BASE] = [self.knowledge_base_score]

        score_df = pd.DataFrame.from_dict(scores, orient="index")
        score_df.columns = ["score"]
        score_df.index.rename("RAG Components", inplace=True)
        score_df.index = score_df.index.map(lambda x: RAGComponents(x).name)
        return score_df

    @property
    def knowledge_base_score(self):
        correctness_by_topic = [topic_score for _, topic_score in self.correctness_by_topic().itertuples()]
        return 1 - (max(correctness_by_topic) - min(correctness_by_topic))

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

    def _get_knowledge_plot(self):
        tabs = [
            TabPanel(child=self._knowledge_base.get_knowledge_plot(), title="Topic exploration"),
            TabPanel(
                child=self._knowledge_base.get_failure_plot(
                    [
                        QuestionSample(**question, id="", reference_context="", conversation_history=[])
                        for question in self._dataframe[
                            ["question", "reference_answer", "agent_answer", "correctness", "metadata"]
                        ].to_dict(orient="records")
                    ]
                ),
                title="Failures",
            ),
        ]

        tabs = Tabs(tabs=tabs, sizing_mode="stretch_width", tabs_location="below")
        return tabs

    def plot_correctness_by_metadata(self, metadata_name: str):
        """
        Create a bokeh plot showing the correctness by a metadata field.
        """
        data = self._correctness_by_metadata(metadata_name)
        metadata_values = data.index.tolist()
        overall_correctness = self.correctness
        correctness = data["correctness"].to_numpy()

        source = ColumnDataSource(
            data={
                "correctness": correctness * 100,
                "metadata_values": metadata_values,
                "colors": get_colors(correctness),
            }
        )

        p = figure(
            y_range=metadata_values,
            height=350,
            toolbar_location=None,
            tools="hover",
            width_policy="max",
        )
        p.hbar(y="metadata_values", right="correctness", source=source, height=0.85, fill_color="#14191B")
        p.hbar(
            y="metadata_values",
            right="correctness",
            source=source,
            height=0.85,
            fill_color="#78BBFA",
            fill_alpha=0.7,
            line_color="white",
            line_width=2,
        )
        vline = Span(
            location=overall_correctness * 100,
            dimension="height",
            line_color="#EA3829",
            line_width=2,
            line_dash="dashed",
        )

        p.add_layout(vline)
        p.background_fill_color = "#14191B"

        p.x_range.start = 0
        r_line = p.line(
            [0],
            [0],
            legend_label="Correctness on the entire Testset",
            line_dash="dashed",
            line_color="#EA3829",
            line_width=2,
        )
        r_line.visible = False  # Set this fake line to invisible
        p.legend.background_fill_color = "#111516"
        p.legend.background_fill_alpha = 0.5

        p.xaxis.axis_label = "Correctness (%)"
        p.title.text_font_size = "14pt"
        p.hover.tooltips = [
            (metadata_name, "@metadata_values"),
            ("Correctness", "@correctness{0.00}"),
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
        if metric_name in self.metric_names:
            if filter_metadata is not None:
                data = self._dataframe[metric_name][
                    self._dataframe["metadata"].apply(lambda x: all(x.get(k) in v for k, v in filter_metadata.items()))
                ]
            else:
                data = self._dataframe[metric_name]

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
                fill_color="#78bbfa",
                line_color="white",
            )
            p.title.text_font_size = "12pt"
            p.hover.tooltips = [
                ("Range", "@left{0.00} to @right{0.00}"),
                ("# questions", "@top"),
            ]

            return p

    def _apply_theme(self, p):
        curdoc().theme = "dark_minimal"
        doc = Document(theme=curdoc().theme)
        doc.add_root(p)
        return p

    def _get_plot_components(self, p):
        script, div = components(self._apply_theme(p), theme="dark_minimal")
        return {"script": script, "div": div}

    def get_metrics_histograms(self):
        histograms_dict = {}
        histograms_dict["Overall"] = {
            "Overall": {
                metric: self._get_plot_components(self.plot_metrics_hist(metric)) for metric in self.metric_names
            }
        }
        histograms_dict["Topics"] = {
            topic: {
                metric: self._get_plot_components(self.plot_metrics_hist(metric, {"topic": [topic]}))
                for metric in self.metric_names
            }
            for topic in self._testset.get_metadata_values("topic")
        }
        histograms_dict["Question"] = {
            q_type: {
                metric: self._get_plot_components(self.plot_metrics_hist(metric, {"question_type": [q_type]}))
                for metric in self.metric_names
            }
            for q_type in self._testset.get_metadata_values("question_type")
        }
        return histograms_dict
