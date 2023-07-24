from typing import Any, Dict

from ..datasets.base import Dataset
from ..ml_worker.core.savable import Artifact
from ..models.base import BaseModel


def _param_to_str(param: Any) -> str:
    if issubclass(type(param), Dataset) or issubclass(type(param), BaseModel):
        return param.name if getattr(param, "name", None) is not None else str(param.id)

    if issubclass(type(param), Artifact):
        return param.meta.name if param.meta.name is not None else str(param.meta.uuid)

    return str(param)


def _params_to_str(params: Dict[str, Any]) -> Dict[str, str]:
    return {key: _param_to_str(value) for key, value in params.items()}


class TestSuiteResultWidget:
    def __init__(self, test_suite_result):
        self.test_suite_result = test_suite_result

    def render_html(self) -> str:
        from jinja2 import Environment, PackageLoader, select_autoescape
        from giskard.visualization.custom_jinja import pluralize, format_metric

        env = Environment(
            loader=PackageLoader("giskard.visualization", "templates"),
            autoescape=select_autoescape(),
        )
        env.filters["pluralize"] = pluralize
        env.filters["format_metric"] = format_metric

        tpl = env.get_template("suite_results.html")

        return tpl.render(
            passed=self.test_suite_result.passed,
            test_results=[
                (name, result, _params_to_str(params)) for name, result, params in self.test_suite_result.results
            ],
            num_passed_tests=len([res for _, res, _ in self.test_suite_result.results if res.passed]),
            num_failed_tests=len(
                [res for _, res, _ in self.test_suite_result.results if not res.passed and not res.is_error]
            ),
            num_error_tests=len([res for _, res, _ in self.test_suite_result.results if res.is_error]),
        )
