from abc import ABC, abstractmethod
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, PackageLoader, select_autoescape

from ..datasets.base import Dataset
from ..ml_worker.core.savable import Artifact
from ..models.base import BaseModel
from ..visualization.custom_jinja import pluralize, format_metric


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

    return env.get_template(file)


class BaseWidget(ABC):
    @abstractmethod
    def render_html(self, **kwargs) -> str:
        pass


class TestSuiteResultWidget(BaseWidget):
    def __init__(self, test_suite_result):
        self.test_suite_result = test_suite_result

    def render_html(self) -> str:
        tpl = get_template("suite_results.html")

        return tpl.render(
            passed=self.test_suite_result.passed,
            test_results=[
                (name, result, _params_to_str(params)) for name, result, params in self.test_suite_result.results
            ],
        )


class ScanResultWidget(BaseWidget):
    def __init__(self, scan_result):
        self.scan_result = scan_result

    def render_html(self, **kwargs) -> str:
        tpl = get_template("scan_results.html")

        issues_by_group = defaultdict(list)
        for issue in self.scan_result.issues:
            issues_by_group[issue.group].append(issue)

        html = tpl.render(
            issues=self.scan_result.issues,
            issues_by_group=issues_by_group,
            num_major_issues={
                group: len([i for i in issues if i.level == "major"]) for group, issues in issues_by_group.items()
            },
            num_medium_issues={
                group: len([i for i in issues if i.level == "medium"]) for group, issues in issues_by_group.items()
            },
            num_info_issues={
                group: len([i for i in issues if i.level == "info"]) for group, issues in issues_by_group.items()
            },
        )

        if kwargs.get("embed", False):
            # Put the HTML in an iframe
            escaped = escape(html)
            uid = id(self)

            with Path(__file__).parent.joinpath("templates", "static", "external.js").open("r") as f:
                js_lib = f.read()

            html = f"""<iframe id="scan-{uid}" srcdoc="{escaped}" style="width: 100%; border: none;" class="gsk-scan"></iframe>
<script>
{js_lib}
(function(){{iFrameResize({{ checkOrigin: false }}, '#scan-{uid}');}})();
</script>"""

        return html
