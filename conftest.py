from typing import List

import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import psutil
import pytest
from _pytest.config.argparsing import Parser
from _pytest.python import Function
from _pytest.reports import TestReport


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    start = time.time()
    process = psutil.Process(os.getpid())

    base_memory_usage = process.memory_info().rss

    yield
    memory_usage = process.memory_info().rss
    fixture_memory_usage = memory_usage - base_memory_usage  # in bytes
    fixture_memory_usage = fixture_memory_usage / (1024 * 1024)  # in mo

    end = time.time()

    file = Path("memory_fixtures.csv")
    write_header = False
    if not file.exists():
        write_header = True
    with file.open("a", encoding="utf-8") as writer:
        if write_header:
            writer.write("fixture_name,execution_time,memory_usage(mo)\n")
        # Add overall test results
        writer.write(f"{request.fixturename},{end - start:.3f},{fixture_memory_usage:.3f}\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: Function, nextitem: Function):
    process = psutil.Process(os.getpid())
    file = Path("memory_tests.csv")
    activate_gc = False
    if activate_gc:
        gc.collect()
        gc.collect()
    base_memory_usage = process.memory_info().rss

    yield
    if activate_gc:
        gc.collect()
        gc.collect()
    memory_usage = process.memory_info().rss
    test_memory_usage = memory_usage - base_memory_usage  # in bytes
    test_memory_usage = test_memory_usage / (1024 * 1024)  # in mo
    full_memory_usage = memory_usage / (1024 * 1024)
    write_header = False
    if not file.exists():
        write_header = True
    with file.open("a", encoding="utf-8") as writer:
        if write_header:
            writer.write("test_name,memory_usage(mo),total_usage(mo)\n")

        # Add overall test results
        writer.write(f"{item.nodeid},{test_memory_usage:.3f},{full_memory_usage:.3f}\n")


# we know this bit is bad, but we cant help it with the current pytest setup
def pytest_addoption(parser: Parser):
    parser.addoption("--use-subprocess", action="store_true", default=False, help="Whether to use subprocess")


def separate_process(item: Function) -> List[TestReport]:
    with NamedTemporaryFile(delete=False) as fp:
        proc = subprocess.run(
            shell=True,
            check=False,
            stdout=sys.stdout,
            stderr=sys.stderr,
            args=f"{sys.executable} -m pytest {item.nodeid} -vvv --tb=long --report-log={fp.name} --no-header --no-summary",
            cwd=Path(__file__).parent,
        )

    reports = []
    try:
        for line in Path(fp.name).read_text().splitlines():
            report_dict = json.loads(line)
            if report_dict["$report_type"] == "TestReport":
                reports.append(TestReport._from_json(report_dict))
        return reports
    finally:
        # Force deletion of the temp file
        Path(fp.name).unlink(missing_ok=True)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: Function):
    if item.get_closest_marker("memory_expensive") and item.config.getoption("--use-subprocess"):
        ihook = item.ihook
        ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
        reports = separate_process(item)
        for rep in reports:
            ihook.pytest_runtest_logreport(report=rep)
        ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
        return True
