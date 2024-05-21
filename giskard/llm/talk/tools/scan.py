from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool

if TYPE_CHECKING:
    from giskard.scanner.report import ScanReport


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
    _output_template: str = "ML model performance issues scanner result:\n {scan_report}"

    def __init__(self, scan_report: ScanReport, name: Optional[str] = None, description: Optional[str] = None):
        """Constructor of the class.

        Parameters
        ----------
        scan_report : ScanReport
            The Giskard ScanReport object.
        name : str, optional
            The name of the Tool.
            If not set, the `default_name` is used.
        description : str, optional
            The description of the Tool.
            If not set, the `default_description` is used.
        """
        super().__init__(name, description)
        self._scan_report = scan_report

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

        Raises
        ------
        AttributeError
            If the 'scan_report' was not provided.
        """
        if not self._scan_report:
            raise AttributeError(
                "To obtain information about issues detected by the Giskard Scan, provide the 'scan_report' argument."
            )
        scan_report = self._scan_report.to_markdown(template="huggingface")
        return self._output_template.format(scan_report=scan_report)
