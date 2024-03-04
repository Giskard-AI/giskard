from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool


class IssuesScannerTool(BaseTool):
    """Issues Scanner Tool.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = "issues_scanner"
    default_description: str = ToolDescription.ISSUES_SCANNER.value
    _output_template: str = "ML model performance issues scanner result:\n {scan_result}"

    @property
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            },
        }

    def __call__(self) -> str:
        """Execute the Tool's functionality.

        Return the Giskard Scan result.

        Returns
        -------
        str
            The Giskard Scan's result.
        """
        scan_result = self._scan_result.to_markdown()
        return self._output_template.format(scan_result=scan_result)
