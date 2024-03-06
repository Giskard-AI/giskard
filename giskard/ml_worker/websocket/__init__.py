from typing import Any, Dict, List, Optional

from enum import Enum
from uuid import UUID

import pydantic
from packaging import version
from pydantic import Field

from giskard.core.validation import ConfiguredBaseModel

IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")


class WorkerReply(ConfiguredBaseModel):
    pass


class Empty(WorkerReply):
    pass


class ErrorReply(WorkerReply):
    error_str: str
    error_type: str
    detail: Optional[str] = None


class ArtifactRef(ConfiguredBaseModel):
    project_key: Optional[str] = None
    id: str
    sample: Optional[bool] = None


class TestFunctionArgument(ConfiguredBaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


class Documentation(ConfiguredBaseModel):
    description: str
    parameters: Dict[str, str]


# CallableMeta shows that all fields can be none,
# but we have a pre-check here for Database constraints except auto-created "version":
# referring to `ai.giskard.domain.Callable` and `ai.giskard.domain.TestFunction`.
class FunctionMeta(ConfiguredBaseModel):
    uuid: str
    name: str
    displayName: Optional[str] = None
    version: Optional[int] = None
    module: Optional[str] = None
    doc: Optional[Documentation] = None
    moduleDoc: Optional[str] = None
    args: Optional[List[TestFunctionArgument]] = None
    tags: Optional[List[str]] = None
    code: str
    type: Optional[str] = None
    debugDescription: Optional[str] = None


# CallableMeta shows that all fields can be none,
# but we have a pre-check here for Database constraints except auto-created "version":
# referring to `ai.giskard.domain.Callable`, `ai.giskard.domain.SlicingFunction`,
# `ai.giskard.domain.TransformationFunction` and `ai.giskard.domain.DatasetProcessFunction`.
class DatasetProcessFunctionMeta(ConfiguredBaseModel):
    uuid: str
    name: str
    displayName: Optional[str] = None
    version: Optional[int] = None
    module: Optional[str] = None
    doc: Optional[Documentation] = None
    moduleDoc: Optional[str] = None
    args: Optional[List[TestFunctionArgument]] = None
    tags: Optional[List[str]] = None
    code: str
    type: Optional[str] = None
    cellLevel: bool
    columnType: Optional[str] = None
    processType: Optional[str] = None


class Catalog(WorkerReply):
    tests: Dict[str, FunctionMeta]
    slices: Dict[str, DatasetProcessFunctionMeta]
    transformations: Dict[str, DatasetProcessFunctionMeta]


class DataRow(ConfiguredBaseModel):
    columns: Dict[str, str]


class DataFrame(ConfiguredBaseModel):
    rows: List[DataRow]


class DatasetRowModificationResult(ConfiguredBaseModel):
    rowId: int
    modifications: Dict[str, str]


class DatasetProcessing(WorkerReply):
    datasetId: str
    totalRows: int
    filteredRows: Optional[List[int]] = None
    modifications: Optional[List[DatasetRowModificationResult]] = None


class FuncArgument(ConfiguredBaseModel):
    name: str
    model: Optional[ArtifactRef] = None
    dataset: Optional[ArtifactRef] = None
    float_arg: Optional[float] = Field(None, alias="float")
    int_arg: Optional[int] = Field(None, alias="int")
    str_arg: Optional[str] = Field(None, alias="str")
    bool_arg: Optional[bool] = Field(None, alias="bool")
    slicingFunction: Optional[ArtifactRef] = None
    transformationFunction: Optional[ArtifactRef] = None
    kwargs: Optional[str] = None
    args: Optional[List["FuncArgument"]] = None
    is_none: bool = Field(..., alias="none")


class DatasetProcessingFunction(ConfiguredBaseModel):
    slicingFunction: Optional[ArtifactRef] = None
    transformationFunction: Optional[ArtifactRef] = None
    arguments: Optional[List[FuncArgument]] = None


class DatasetProcessingParam(ConfiguredBaseModel):
    dataset: ArtifactRef
    functions: Optional[List[DatasetProcessingFunction]] = None


class EchoMsg(WorkerReply):
    msg: str


class EchoResponse(WorkerReply):
    msg: str
    job_ids: List[UUID]


class Explanation(ConfiguredBaseModel):
    per_feature: Dict[str, float]


class Explain(WorkerReply):
    explanations: Dict[str, Explanation]


class ExplainParam(ConfiguredBaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    columns: Dict[str, str]


class WeightsPerFeature(ConfiguredBaseModel):
    weights: Optional[List[float]] = None


class ExplainText(WorkerReply):
    words: Optional[List[str]] = None
    weights: Dict[str, WeightsPerFeature]


class ExplainTextParam(ConfiguredBaseModel):
    model: ArtifactRef
    feature_name: str
    columns: Dict[str, Optional[str]]
    column_types: Dict[str, str]


class GeneratedTestInput(ConfiguredBaseModel):
    name: str
    value: str
    is_alias: bool


class GeneratedTestSuite(ConfiguredBaseModel):
    test_uuid: str
    inputs: Optional[List[GeneratedTestInput]] = None


class GenerateTestSuite(WorkerReply):
    tests: Optional[List[GeneratedTestSuite]] = None


class ModelMeta(ConfiguredBaseModel):
    model_type: Optional[str] = None

    if IS_PYDANTIC_V2:

        class Config:
            protected_namespaces = ()  # Disable pydantic warning


class DatasetMeta(ConfiguredBaseModel):
    target: Optional[str] = None


class SuiteInput(ConfiguredBaseModel):
    name: str
    type: str
    modelMeta: Optional[ModelMeta] = None
    datasetMeta: Optional[DatasetMeta] = None


class GenerateTestSuiteParam(ConfiguredBaseModel):
    project_key: str
    inputs: Optional[List[SuiteInput]] = None


class Platform(ConfiguredBaseModel):
    machine: str
    node: str
    processor: str
    release: str
    system: str
    version: str


class GetInfo(WorkerReply):
    platform: Platform
    interpreter: str
    interpreterVersion: str
    installedPackages: Dict[str, str]
    kernelName: str
    pid: int
    processStartTime: int
    giskardClientVersion: str


class GetInfoParam(ConfiguredBaseModel):
    list_packages: bool


class AbortParams(ConfiguredBaseModel):
    job_id: UUID


class GetLogsParams(ConfiguredBaseModel):
    job_id: UUID
    nb_last_lines: int


class GetLogs(ConfiguredBaseModel):
    logs: str


class TestMessageType(str, Enum):
    ERROR = "ERROR"
    INFO = "INFO"


class TestMessage(ConfiguredBaseModel):
    type: TestMessageType
    text: str


class PartialUnexpectedCounts(ConfiguredBaseModel):
    value: Optional[List[int]] = None
    count: int


class SingleTestResultDetails(ConfiguredBaseModel):
    inputs: Dict[str, List[Any]]
    outputs: List[Any]
    results: List[Any]
    metadata: Dict[str, List[Any]]


class SingleTestResult(ConfiguredBaseModel):
    passed: bool
    is_error: Optional[bool] = None
    messages: Optional[List[TestMessage]] = None
    props: Optional[Dict[str, str]] = None
    metric: Optional[float] = None
    metric_name: Optional[str] = None
    failed_indexes: Optional[Dict[str, List[int]]] = None
    details: Optional[SingleTestResultDetails] = None


class IdentifierSingleTestResult(ConfiguredBaseModel):
    id: int
    result: SingleTestResult
    arguments: Optional[List[FuncArgument]] = None


class NamedSingleTestResult(ConfiguredBaseModel):
    testUuid: str
    result: SingleTestResult


class RunAdHocTest(WorkerReply):
    results: Optional[List[NamedSingleTestResult]] = None


class RunAdHocTestParam(ConfiguredBaseModel):
    testUuid: str
    arguments: Optional[List[FuncArgument]] = None
    debug: Optional[bool] = None
    projectKey: Optional[str] = None


class RunModelForDataFrame(WorkerReply):
    all_predictions: Optional[DataFrame] = None
    prediction: Optional[List[str]] = None
    probabilities: Optional[List[float]] = None
    raw_prediction: Optional[List[float]] = None


class RunModelForDataFrameParam(ConfiguredBaseModel):
    model: ArtifactRef
    dataframe: DataFrame
    target: Optional[str] = None
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]


class RunModelParam(ConfiguredBaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    inspectionId: int
    project_key: str


class SuiteTestArgument(ConfiguredBaseModel):
    id: int
    testUuid: str
    arguments: Optional[List[FuncArgument]] = None


class TestSuite(WorkerReply):
    is_error: bool
    is_pass: bool
    results: Optional[List[IdentifierSingleTestResult]] = None


class TestSuiteParam(ConfiguredBaseModel):
    projectKey: str
    tests: Optional[List[SuiteTestArgument]] = None
    globalArguments: Optional[List[FuncArgument]] = None


class PushKind(str, Enum):
    PERTURBATION = "PERTURBATION"
    CONTRIBUTION = "CONTRIBUTION"
    OVERCONFIDENCE = "OVERCONFIDENCE"
    UNDERCONFIDENCE = "UNDERCONFIDENCE"


class CallToActionKind(str, Enum):
    NONE = "NONE"
    CREATE_SLICE = "CREATE_SLICE"
    CREATE_TEST = "CREATE_TEST"
    CREATE_PERTURBATION = "CREATE_PERTURBATION"
    SAVE_PERTURBATION = "SAVE_PERTURBATION"
    CREATE_ROBUSTNESS_TEST = "CREATE_ROBUSTNESS_TEST"
    CREATE_SLICE_OPEN_DEBUGGER = "CREATE_SLICE_OPEN_DEBUGGER"
    OPEN_DEBUGGER_UNDERCONFIDENCE = "OPEN_DEBUGGER_UNDERCONFIDENCE"
    ADD_TEST_TO_CATALOG = "ADD_TEST_TO_CATALOG"
    SAVE_EXAMPLE = "SAVE_EXAMPLE"
    OPEN_DEBUGGER_OVERCONFIDENCE = "OPEN_DEBUGGER_OVERCONFIDENCE"
    CREATE_UNIT_TEST = "CREATE_UNIT_TEST"


class GetPushParam(ConfiguredBaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    dataframe: Optional[DataFrame] = None
    target: Optional[str] = None
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]
    push_kind: Optional[PushKind] = None
    cta_kind: Optional[CallToActionKind] = None
    rowIdx: int


class PushDetails(ConfiguredBaseModel):
    action: str
    explanation: str
    button: str
    cta: CallToActionKind


class Push(ConfiguredBaseModel):
    kind: PushKind
    key: Optional[str] = None
    value: Optional[str] = None
    push_title: str
    push_details: List[PushDetails]


class PushAction(ConfiguredBaseModel):
    object_uuid: str
    arguments: Optional[List[FuncArgument]] = None


class GetPushResponse(ConfiguredBaseModel):
    contribution: Optional[Push] = None
    perturbation: Optional[Push] = None
    overconfidence: Optional[Push] = None
    underconfidence: Optional[Push] = None
    action: Optional[PushAction] = None


class CreateSubDatasetParam(ConfiguredBaseModel):
    projectKey: str
    sample: bool
    name: str
    copiedRows: Dict[str, List[int]]


class CreateDatasetParam(ConfiguredBaseModel):
    projectKey: str
    name: str
    headers: List[str]
    rows: List[List[str]]


class CreateSubDataset(WorkerReply):
    datasetUuid: str
