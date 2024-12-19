import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
from avidtools.datamodels.components import ArtifactTypeEnum

from giskard.scanner.issues import Harmfulness, Issue, IssueLevel, Performance
from giskard.scanner.report import ScanReport


def test_scan_report_can_be_exported_to_avid():
    model = Mock()
    model.name = "My Test Model"
    dataset = Mock()
    dataset.meta.name = "My Test Dataset"

    issues = [
        Issue(
            model,
            dataset,
            Harmfulness,
            IssueLevel.MAJOR,
            description="This is a test issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204", "avid-effect:ethics:E0301"],
        ),
        Issue(
            model,
            dataset,
            Performance,
            IssueLevel.MEDIUM,
            description="There is a performance issue",
            meta={"metric": "Accuracy", "metric_value": 0.1},
            taxonomy=["avid-effect:performance:P0204"],
        ),
        Issue(
            model,
            dataset,
            Performance,
            IssueLevel.MINOR,
            description="There is a minor issue",
            meta={},
            taxonomy=["avid-effect:performance:P0204"],
        ),
    ]
    report = ScanReport(issues=issues, model=model, dataset=dataset)
    avid_reports = report.to_avid()

    assert len(avid_reports) == 3

    for r in avid_reports:
        assert r.affects.artifacts[0].name == "My Test Model"
        assert r.affects.artifacts[0].type == ArtifactTypeEnum.model
        assert r.affects.artifacts[1].name == "My Test Dataset"
        assert r.affects.artifacts[1].type == ArtifactTypeEnum.dataset
        assert "Giskard" in r.references[0].label

    assert avid_reports[0].problemtype.description.value == "This is a test issue"
    assert avid_reports[0].metrics[0].name == "FPR"
    assert avid_reports[0].metrics[0].results == {"value": 0.23}
    assert len(avid_reports[0].impact.avid.sep_view) == 2
    assert avid_reports[0].impact.avid.sep_view[0].value == "P0204: Accuracy"
    assert avid_reports[0].impact.avid.sep_view[1].value == "E0301: Toxicity"
    assert set(avid_reports[0].impact.avid.risk_domain) == set(["Performance", "Ethics"])

    assert avid_reports[1].problemtype.description.value == "There is a performance issue"
    assert avid_reports[1].metrics[0].name == "Accuracy"

    assert avid_reports[2].metrics is None
    assert avid_reports[2].problemtype.description.value == "There is a minor issue"

    # Check that we can write the AVID report to file and read it back
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir).joinpath("test_report.avid")
        report.to_avid(dest_path)

        with dest_path.open("r", encoding="utf-8") as f:
            avid_reports_read = [json.loads(line) for line in f.readlines()]

    assert len(avid_reports_read) == len(avid_reports)


def test_avid_artifacts_from_scan_report():
    model = Mock()
    model.name = "My Test Model"

    # Dataset with no name should not be included
    dataset = Mock()
    dataset.meta.name = None
    issues = [
        Issue(
            model,
            dataset,
            Harmfulness,
            IssueLevel.MAJOR,
            description="This is a test issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204", "avid-effect:ethics:E0301"],
        ),
    ]
    report = ScanReport(issues=issues, model=model, dataset=dataset)
    assert len(report.to_avid()[0].affects.artifacts) == 1
    assert report.to_avid()[0].affects.artifacts[0].name == "My Test Model"

    # No dataset
    issues = [
        Issue(
            model,
            None,
            Harmfulness,
            IssueLevel.MAJOR,
            description="This is a test issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204", "avid-effect:ethics:E0301"],
        ),
    ]
    report = ScanReport(issues=issues, model=model, dataset=dataset)
    assert len(report.to_avid()[0].affects.artifacts) == 1

    # Dataset and model with names are both included
    model.name = "My Test Model"
    dataset.meta.name = "My Test Dataset"
    issues = [
        Issue(
            model,
            dataset,
            Harmfulness,
            IssueLevel.MAJOR,
            description="This is a test issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204", "avid-effect:ethics:E0301"],
        ),
    ]
    report = ScanReport(issues=issues, model=model, dataset=dataset)
    assert len(report.to_avid()[0].affects.artifacts) == 2


def test_avid_report_includes_examples():
    model = Mock()
    model.name = "My Test Model"
    dataset = Mock()
    dataset.meta.name = "My Test Dataset"

    issues = [
        Issue(
            model,
            dataset,
            Harmfulness,
            IssueLevel.MAJOR,
            description="This is a test issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204", "avid-effect:ethics:E0301"],
        ),
        Issue(
            model,
            dataset,
            Performance,
            IssueLevel.MINOR,
            description="There is a minor issue",
            meta={"metric": "FPR", "metric_value": 0.23},
            taxonomy=["avid-effect:performance:P0204"],
            examples=pd.DataFrame({"feature": [1, 2], "value": ["a", "b"]}),
        ),
    ]

    report = ScanReport(issues=issues, model=model, dataset=dataset)
    r1, r2 = report.to_avid()

    assert "examples" not in r1.metrics[0].results
    assert "examples" in r2.metrics[0].results
    assert r2.metrics[0].results["examples"] == [{"feature": 1, "value": "a"}, {"feature": 2, "value": "b"}]
