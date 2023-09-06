from typing import Sequence

import markdown
from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup

from ..utils.display import format_number


class IncludeRawExtension(Extension):
    tags = {"include_raw"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        template = parser.parse_expression()
        result = self.call_method("_render", [template], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, filename):
        return Markup(self.environment.loader.get_source(self.environment, filename)[0])


def markdown_to_html(md_text):
    html = markdown.markdown(md_text)
    return Markup(html)


def pluralize(count, singular="", plural="s"):
    if isinstance(count, Sequence):
        count = len(count)
    return singular if count == 1 else plural


def format_metric(value, n=3):
    return format_number(value, n)
