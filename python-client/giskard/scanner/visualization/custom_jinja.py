from typing import Sequence
from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup


class IncludeRawExtension(Extension):
    tags = {"include_raw"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        template = parser.parse_expression()
        result = self.call_method("_render", [template], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, filename):
        return Markup(self.environment.loader.get_source(self.environment, filename)[0])


def pluralize(count, singular="", plural="s"):
    if isinstance(count, Sequence):
        count = len(count)
    return singular if count == 1 else plural


def format_metric(value, n=3):
    if isinstance(value, float):
        if value > 1e6 or value < 1e-3:
            return f"{value:.{n}e}"
        else:
            return f"{value:.{3}f}"

    if isinstance(value, int) and abs(value) > 1e4:
        return f"{value:.{n}e}"

    return value
