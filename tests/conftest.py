from glob import glob
from io import TextIOWrapper
from pathlib import Path
from typing import List, Tuple
import os
from uuid import uuid4

from _pytest.terminal import TerminalReporter
from _pytest.config import ExitCode, Config
from _pytest.reports import BaseReport
from pytest import CollectReport, TestReport

pytest_plugins = []
for f in glob("**/fixtures/**/*.py", recursive=True):
    path = Path(f)
    pytest_plugins.append(".".join([*path.parts[:-1], path.stem]))


def pytest_collection_modifyitems(session, config, items):
    # Only considers functions inside /tests directory as unit tests
    # otherwise test functions in the main part of the repo are also detected
    items[:] = [i for i in items if i.location[0].startswith("tests")]


def _write_details(writer: TextIOWrapper, title: str, content: str):
    if content:
        writer.write("<details>\n")
        writer.write(f"<summary>{title}</summary>\n\n")
        writer.write(f"```\n{content}\n```\n")
        writer.write("\n</details>\n")


def _write_report(writer: TextIOWrapper, report: BaseReport):
    writer.write(f"\n\n<h4 id=user-content-{report.html_id}>{report.nodeid}</h4>\n\n")
    writer.write(f"```python\n{report.longreprtext}\n```\n")
    _write_details(writer, "Log", report.caplog)
    _write_details(writer, "Stdout", report.capstdout)
    _write_details(writer, "Stderr", report.capstderr)


def pytest_terminal_summary(
    terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config
):
    file = Path(os.getenv("GITHUB_STEP_SUMMARY", "local_report.md"))

    with file.open("w", encoding="utf-8") as writer:
        # Add overall test results
        writer.write("### Pytest report\n")
        writer.write(
            f"Test results: {ExitCode(exitstatus).name} {'✅' if exitstatus == ExitCode.OK else '❌'}\n\n"
        )

        writer.write("\n| Status |Count |\n")
        writer.write("| :---: | :---: |\n")
        # Ignore warnings and compute stats for other status

        total = 0
        for k, v in terminalreporter.stats.items():
            if not k or k == "warnings":
                continue
            total += len(v)
            writer.write(f"| {k.capitalize()} | {len(v)} |\n")
        writer.write(f"| Total | {total} |\n\n")

        # Extract failures and errors to get more details
        failures: List[TestReport] = [
            report for report in terminalreporter.stats.get("failed", [])
        ]
        errors: List[CollectReport] = [
            report for report in terminalreporter.stats.get("error", [])
        ]

        # Write a summary of all test, to easily check is one test ran or not
        writer.write("### All tests results\n\n")
        writer.write("<details>\n")
        writer.write("<summary>Expand here</summary>\n\n")

        all_tests: List[Tuple[str, str]] = [
            (v.nodeid, k)
            for k, report_list in terminalreporter.stats.items()
            if k and k != "warnings"
            for v in report_list
        ]
        for name, status in sorted(all_tests, key=lambda elt: elt[0]):
            writer.write(f"- {name} {status.upper()}\n")
        writer.write("\n</details>\n\n")

        # Create a list to get easy access to an error
        # Note: html id/anchor must be prefixed by user-content- for Github
        writer.write("### Summary of failures and errors\n\n")
        for error in errors:
            error.html_id = str(uuid4())
            writer.write(
                f"- [Error : {error.nodeid.split('::')[-1]}](#user-content-{error.html_id})\n"
            )
        for failure in failures:
            failure.html_id = str(uuid4())
            writer.write(
                f"- [Failure : {failure.nodeid.split('::')[-1]}](#user-content-{failure.html_id})\n"
            )

        writer.write("\n### Errors\n\n")
        for error in errors:
            _write_report(writer, error)

        writer.write("\n### Failures\n\n")
        for failure in failures:
            _write_report(writer, failure)
