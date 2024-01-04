from typing import Any, Dict

from abc import ABC, abstractmethod
from collections import defaultdict
from html import escape
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..core.savable import Artifact
from ..datasets.base import Dataset
from ..models.base import BaseModel
from ..scanner.issues import IssueLevel
from ..visualization.custom_jinja import format_metric, markdown_to_html, pluralize


def _param_to_str(param: Any) -> str:
    if issubclass(type(param), Dataset) or issubclass(type(param), BaseModel):
        return param.name if getattr(param, "name", None) is not None else str(param.id)

    if issubclass(type(param), Artifact):
        return param.meta.name if param.meta.name is not None else str(param.meta.uuid)

    return str(param)


def _params_to_str(params: Dict[str, Any]) -> Dict[str, str]:
    return {key: _param_to_str(value) for key, value in params.items()}


def get_template(file: str):
    env = Environment(
        loader=PackageLoader("giskard.visualization", "templates"),
        autoescape=select_autoescape(),
    )
    env.filters["pluralize"] = pluralize
    env.filters["format_metric"] = format_metric
    env.filters["markdown"] = markdown_to_html

    return env.get_template(file)


class BaseWidget(ABC):
    @abstractmethod
    def render_html(self, **kwargs) -> str:
        pass


class TestSuiteResultWidget(BaseWidget):
    def __init__(self, test_suite_result):
        self.test_suite_result = test_suite_result

    def render_html(self) -> str:
        tpl = get_template("suite_results/suite_results.html")

        return tpl.render(
            passed=self.test_suite_result.passed,
            test_results=[
                (name, result, _params_to_str(params)) for name, result, params in self.test_suite_result.results
            ],
        )


class ScanReportWidget(BaseWidget):
    def __init__(self, scan_result):
        self.scan_result = scan_result

    def render_template(self, template_filename: str, **kwargs) -> str:
        tpl = get_template("scan_report/" + template_filename)

        issues_by_group = defaultdict(list)
        for issue in self.scan_result.issues:
            issues_by_group[issue.group].append(issue)

        groups = []
        for group, issues in issues_by_group.items():
            groups.append(
                {
                    "group": group,
                    "issues": issues,
                    "num_major_issues": len([i for i in issues if i.level == IssueLevel.MAJOR]),
                    "num_medium_issues": len([i for i in issues if i.level == IssueLevel.MEDIUM]),
                    "num_minor_issues": len([i for i in issues if i.level == IssueLevel.MINOR]),
                }
            )

        return tpl.render(
            issues=self.scan_result.issues,
            groups=groups,
            **kwargs,
        )

    def render_html(self, template="full", embed=False) -> str:
        html = self.render_template(f"html/{template}.html")

        if embed:
            # Put the HTML in an iframe
            escaped = escape(html)
            uid = id(self)

            with Path(__file__).parent.joinpath("templates", "scan_report", "html", "static", "external.js").open(
                "r"
            ) as f:
                js_lib = f.read()

            html = f"""<iframe id="scan-{uid}" srcdoc="{escaped}" style="width: 100%; border: none;" class="gsk-scan"></iframe>
<script>
{js_lib}
(function(){{iFrameResize({{ checkOrigin: false }}, '#scan-{uid}');}})();
</script>"""

        return html

    def render_markdown(self, template="full") -> str:
        return self.render_template(f"markdown/{template}.md")
