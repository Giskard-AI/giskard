from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool


class IssuesScannerTool(BaseTool):
    default_name: str = "issues_scanner"
    default_description: str = ToolDescription.ISSUES_SCANNER.value
    _output_template: str = "ML model performance issues scanner result:\n {scan_result}"

    @property
    def specification(self) -> str:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            },
        }

    def __call__(self) -> str:
        scan_result = self._scan_result.to_markdown()
        return self._output_template.format(scan_result=scan_result)
