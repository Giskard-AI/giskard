import datetime

import giskard

from ..core.errors import GiskardImportError
from ..datasets import Dataset
from ..models.base import BaseModel
from ..scanner.issues import Issue

try:
    from avidtools.datamodels.components import (
        Artifact,
        ArtifactTypeEnum,
        AvidTaxonomy,
        ClassEnum,
        Detection,
        Impact,
        LangValue,
        LifecycleEnum,
        MethodEnum,
        Metric,
        Problemtype,
        Reference,
        SepEnum,
        TypeEnum,
    )
    from avidtools.datamodels.report import Affects, Report
except ImportError:
    raise GiskardImportError("Avidtools is not installed. Please install it with `pip install avidtools`.")


def create_report_from_issue(issue: Issue, model: BaseModel, dataset: Dataset = None) -> Report:
    """Create a report from an issue.

    Parameters
    ----------
    issue : Issue
        Issue to create a report from.
    model : BaseModel
        Model that was evaluated.
    dataset : Dataset, optional
        Dataset that was used for evaluation, by default ``None``.

    Returns
    -------
    Report
        AVID Report created from the issue.
    """
    # Prepare artifacts
    artifacts = [Artifact(type=ArtifactTypeEnum.model, name=model.name)]
    if dataset and dataset.meta.name:
        artifacts.append(Artifact(type=ArtifactTypeEnum.dataset, name=dataset.meta.name))

    affects = Affects(
        developer=[],
        deployer=[],
        artifacts=artifacts,
    )
    references = [Reference(type="source", label="Giskard Scanner", url="https://giskard.ai")]

    report = Report(
        affects=affects,
        references=references,
        reported_date=datetime.date.today(),
    )
    report.description = LangValue(
        lang="eng", value=f"The model was evaluated by the Giskard Scanner {giskard.__version__}."
    )
    report.problemtype = Problemtype(
        classof=ClassEnum.llm if model.is_text_generation else ClassEnum.na,
        type=TypeEnum.detection,
        description=LangValue(lang="eng", value=issue.description),
        credit=[LangValue(lang="eng", value="Giskard")],
    )
    if issue.meta.get("metric"):
        report.metrics = [
            Metric(
                name=issue.meta.get("metric"),
                detection_method=Detection(type=MethodEnum.thres, name=f"Giskard Scanner {giskard.__version__}"),
                results={"value": issue.meta.get("metric_value")},
            )
        ]

    tags = [tag.split(":") for tag in issue.taxonomy if tag.startswith("avid-effect:")]
    risk_domain = list(set([rd.title() for _, rd, _ in tags]))
    sep_view = [SepEnum[sep.upper()] for _, _, sep in tags]

    report.impact = Impact(
        avid=AvidTaxonomy(
            vuln_id=None,
            risk_domain=risk_domain,
            sep_view=sep_view,
            lifecycle_view=[LifecycleEnum.L05],  # L05: Evaluation
            taxonomy_version="0.2",
        )
    )

    return report
