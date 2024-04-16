from typing import Sequence

import numpy as np

from ..llm.errors import LLMImportError

try:
    import textwrap

    from bokeh.models import ColumnDataSource, HoverTool, LabelSet
    from bokeh.palettes import Category20
    from bokeh.plotting import figure
except ImportError as err:
    raise LLMImportError(flavor="llm") from err


def get_failure_plot(knowledge_base, question_evaluation: Sequence = None):
    document_ids = [question.metadata["seed_document_id"] for question in question_evaluation]
    knowledge_base._reduced_embeddings
    reduced_embeddings = np.stack(
        [knowledge_base._documents_index[doc_id].reduced_embeddings for doc_id in document_ids]
    )

    topics = [question.metadata["topic"] for question in question_evaluation]
    failure_palette = ["#ba0e0e", "#0a980a"]
    questions = [question.question for question in question_evaluation]
    agent_answer = [question.agent_answer for question in question_evaluation]
    reference_answer = [question.reference_answer for question in question_evaluation]
    correctness = [question.correctness for question in question_evaluation]
    colors = [failure_palette[question.correctness] for question in question_evaluation]

    x_min = knowledge_base._reduced_embeddings[:, 0].min()
    x_max = knowledge_base._reduced_embeddings[:, 0].max()
    y_min = knowledge_base._reduced_embeddings[:, 1].min()
    y_max = knowledge_base._reduced_embeddings[:, 1].max()

    x_range = (x_min - (x_max - x_min) * 0.05, x_max + (x_max - x_min) * 0.6)
    y_range = (y_min - (y_max - y_min) * 0.25, y_max + (y_max - y_min) * 0.25)

    source = ColumnDataSource(
        data={
            "x": reduced_embeddings[:, 0],
            "y": reduced_embeddings[:, 1],
            "topic": [textwrap.fill(t) for t in topics],
            "correctness": correctness,
            "questions": questions,
            "agent_answer": agent_answer,
            "reference_answer": reference_answer,
            "id": document_ids,
            "content": [
                knowledge_base[doc_id].content
                if len(knowledge_base[doc_id].content) < 500
                else knowledge_base[doc_id].content[:500] + "..."
                for doc_id in document_ids
            ],
            "color": colors,
        }
    )

    hover = HoverTool(
        mode="mouse",
        tooltips="""
    <div style="width:400px;">
    <b>Document id:</b> @id <br>
    <b>Topic:</b> @topic <br>
    <b>Question:</b> @questions <br>
    <b>agent Answer:</b> @agent_answer <br>
    <b>Reference Answer:</b> @reference_answer <br>
    <b>Correctness:</b> @correctness <br>
    <b>Content:</b> @content
    </div>
    """,
    )

    p = figure(
        tools=["pan", "wheel_zoom", "box_zoom", "reset", "save"],
        toolbar_location="right",
        x_range=x_range,
        y_range=y_range,
        sizing_mode="stretch_width",
    )
    p.add_tools(hover)
    p.toolbar.logo = "grey"
    p.background_fill_color = "#14191B"
    p.grid.grid_line_color = "white"

    foreground_scatter = p.scatter(
        x="x",
        y="y",
        source=source,
        color="color",
        line_color="color",
        line_alpha=1.0,
        line_width=2,
        alpha=0.7,
        size=6,
        legend_group="correctness",
    )

    hover.renderers = [foreground_scatter]

    p.legend.location = "top_right"
    p.legend.title = "Question Correctness"
    p.legend.title_text_font_style = "bold"
    p.legend.background_fill_color = "#111516"
    p.legend.background_fill_alpha = 0.5
    p.title.text_font_size = "14pt"
    p.legend.title_text_color = "#B1B1B1"

    background_source = ColumnDataSource(
        data={
            "x": knowledge_base._reduced_embeddings[:, 0],
            "y": knowledge_base._reduced_embeddings[:, 1],
        }
    )

    p.scatter(
        x="x",
        y="y",
        source=background_source,
        color="grey",
        alpha=0.2,
        size=6,
    )
    if len(knowledge_base.topics) > 1:
        topic_centers = np.array(
            [
                np.mean(
                    [
                        doc.reduced_embeddings
                        for _, doc in knowledge_base._documents_index.items()
                        if doc.topic_id == topic_id
                    ],
                    axis=0,
                )
                for topic_id in range(len(knowledge_base.topics) - 1)
            ]
        )
        topics = [knowledge_base.topics[topic_id] for topic_id in range(len(knowledge_base.topics) - 1)]
        label_source = ColumnDataSource(
            data={
                "x": topic_centers[:, 0],
                "y": topic_centers[:, 1],
                "topic": topics,
            }
        )

        labels = LabelSet(
            x="x",
            y="y",
            text="topic",
            level="glyph",
            text_align="center",
            text_font_size="12pt",
            text_font_style="bold",
            text_color="#B1B1B1",
            source=label_source,
        )
        p.add_layout(labels)

    return p


def get_knowledge_plot(knowledge_base):
    if knowledge_base.topics is None:
        raise ValueError("No topics found.")

    TOOLS = "hover,pan,wheel_zoom,box_zoom,reset,save"

    topics_ids = [doc.topic_id for doc in knowledge_base._documents]
    palette = Category20[20]

    colors = np.array([palette[topic % 20] if topic >= 0 else "#999" for topic in topics_ids])

    x_min = knowledge_base._reduced_embeddings[:, 0].min()
    x_max = knowledge_base._reduced_embeddings[:, 0].max()
    y_min = knowledge_base._reduced_embeddings[:, 1].min()
    y_max = knowledge_base._reduced_embeddings[:, 1].max()

    x_range = (x_min - (x_max - x_min) * 0.05, x_max + (x_max - x_min) * 0.6)
    y_range = (y_min - (y_max - y_min) * 0.25, y_max + (y_max - y_min) * 0.25)

    source = ColumnDataSource(
        data={
            "x": knowledge_base._reduced_embeddings[:, 0],
            "y": knowledge_base._reduced_embeddings[:, 1],
            "topic": [textwrap.fill(knowledge_base.topics[topic_id], 40) for topic_id in topics_ids],
            "id": [doc.id for doc in knowledge_base._documents],
            "content": [
                doc.content if len(doc.content) < 500 else doc.content[:500] + "..."
                for doc in knowledge_base._documents
            ],
            "color": colors,
        }
    )
    p = figure(
        tools=TOOLS,
        toolbar_location="right",
        x_range=x_range,
        y_range=y_range,
        sizing_mode="stretch_width",
    )
    p.toolbar.logo = "grey"
    p.background_fill_color = "#14191B"
    p.grid.grid_line_color = "white"

    p.hover.tooltips = """
    <div style="width:400px;">
    <b>Document id:</b> @id <br>
    <b>Topic:</b> @topic <br>
    <b>Document Content:</b> @content
    </div>
    """

    p.scatter(
        x="x",
        y="y",
        source=source,
        color="color",
        line_color="color",
        line_alpha=1.0,
        line_width=2,
        alpha=0.7,
        size=6,
        legend_group="topic",
    )
    p.legend.location = "top_right"
    p.legend.title = "Knowledge Base Tospics"
    p.legend.title_text_font_style = "bold"
    p.legend.background_fill_color = "#111516"
    p.legend.background_fill_alpha = 0.5
    p.legend.title_text_color = "#B1B1B1"

    p.title.text_font_size = "14pt"

    return p
