from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WorkerReply(BaseModel):
    pass


class Empty(WorkerReply):
    pass


class ErrorReply(WorkerReply):
    error_str: str
    error_type: str
    detail: Optional[str] = None


class ArtifactRef(BaseModel):
    project_key: Optional[str] = None
    id: str
    sample: Optional[bool] = None


class TestFunctionArgument(BaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


# CallableMeta shows that all fields can be none
class FunctionMeta(BaseModel):
    uuid: str
    name: Optional[str] = None
    displayName: Optional[str] = None
    version: Optional[int] = None
    module: Optional[str] = None
    doc: Optional[str] = None
    moduleDoc: Optional[str] = None
    args: Optional[List[TestFunctionArgument]] = None
    tags: Optional[List[str]] = None
    code: Optional[str] = None
    type: Optional[str] = None


class DatasetProcessFunctionMeta(BaseModel):
    uuid: str
    name: Optional[str] = None
    displayName: Optional[str] = None
    version: Optional[int] = None  # For backward compatibility
    module: Optional[str] = None
    doc: Optional[str] = None
    moduleDoc: Optional[str] = None
    args: Optional[List[TestFunctionArgument]] = None
    tags: Optional[List[str]] = None
    code: Optional[str] = None
    type: Optional[str] = None
    cellLevel: Optional[bool] = None
    columnType: Optional[str] = None
    processType: Optional[str] = None


class Catalog(WorkerReply):
    tests: Dict[str, FunctionMeta]
    slices: Dict[str, DatasetProcessFunctionMeta]
    transformations: Dict[str, DatasetProcessFunctionMeta]


class DataRow(BaseModel):
    columns: Dict[str, str]


class DataFrame(BaseModel):
    rows: List[DataRow]


class DatasetRowModificationResult(BaseModel):
    rowId: int
    modifications: Dict[str, str]


class DatasetProcessing(WorkerReply):
    datasetId: str
    totalRows: int
    filteredRows: Optional[List[int]] = None
    modifications: Optional[List[DatasetRowModificationResult]] = None


class FuncArgument(BaseModel):
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


class DatasetProcessingFunction(BaseModel):
    slicingFunction: Optional[ArtifactRef] = None
    transformationFunction: Optional[ArtifactRef] = None
    arguments: Optional[List[FuncArgument]] = None


class DatasetProcessingParam(BaseModel):
    dataset: ArtifactRef
    functions: Optional[List[DatasetProcessingFunction]] = None


class EchoMsg(WorkerReply):
    msg: str


class Explanation(BaseModel):
    per_feature: Dict[str, float]


class Explain(WorkerReply):
    explanations: Dict[str, Explanation]


class ExplainParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    columns: Dict[str, str]


class WeightsPerFeature(BaseModel):
    weights: Optional[List[float]] = None


class ExplainText(WorkerReply):
    words: Optional[List[str]] = None
    weights: Dict[str, WeightsPerFeature]


class ExplainTextParam(BaseModel):
    model: ArtifactRef
    feature_name: str
    columns: Dict[str, str]
    column_types: Dict[str, str]


class GeneratedTestInput(BaseModel):
    name: str
    value: str
    is_alias: bool


class GeneratedTestSuite(BaseModel):
    test_uuid: str
    inputs: Optional[List[GeneratedTestInput]] = None


class GenerateTestSuite(WorkerReply):
    tests: Optional[List[GeneratedTestSuite]] = None


class ModelMeta(BaseModel):
    model_type: Optional[str] = None


class DatasetMeta(BaseModel):
    target: Optional[str] = None


class SuiteInput(BaseModel):
    name: str
    type: str
    modelMeta: Optional[ModelMeta] = None
    datasetMeta: Optional[DatasetMeta] = None


class GenerateTestSuiteParam(BaseModel):
    project_key: str
    inputs: Optional[List[SuiteInput]] = None


class Platform(BaseModel):
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
    mlWorkerId: str
    isRemote: bool
    pid: int
    processStartTime: int
    giskardClientVersion: str


class GetInfoParam(BaseModel):
    list_packages: bool


class TestMessageType(Enum):
    ERROR = 0
    INFO = 1


class TestMessage(BaseModel):
    type: TestMessageType
    text: str


class PartialUnexpectedCounts(BaseModel):
    value: Optional[List[int]] = None
    count: int


class SingleTestResult(BaseModel):
    passed: bool
    is_error: Optional[bool] = None
    messages: Optional[List[TestMessage]] = None
    props: Optional[Dict[str, str]] = None
    metric: Optional[float] = None
    missing_count: Optional[int] = None
    missing_percent: Optional[float] = None
    unexpected_count: Optional[int] = None
    unexpected_percent: Optional[float] = None
    unexpected_percent_total: Optional[float] = None
    unexpected_percent_nonmissing: Optional[float] = None
    partial_unexpected_index_list: Optional[List[int]] = None
    partial_unexpected_counts: Optional[List[PartialUnexpectedCounts]] = None
    unexpected_index_list: Optional[List[int]] = None
    output_df: Optional[bytes] = None
    number_of_perturbed_rows: Optional[int] = None
    actual_slices_size: Optional[List[int]] = None
    reference_slices_size: Optional[List[int]] = None
    output_df_id: Optional[str] = None


class IdentifierSingleTestResult(BaseModel):
    id: int
    result: SingleTestResult
    arguments: Optional[List[FuncArgument]] = None


class NamedSingleTestResult(BaseModel):
    testUuid: str
    result: SingleTestResult


class RunAdHocTest(WorkerReply):
    results: Optional[List[NamedSingleTestResult]] = None


class RunAdHocTestParam(BaseModel):
    testUuid: str
    arguments: Optional[List[FuncArgument]] = None
    debug: Optional[bool] = None


class RunModelForDataFrame(WorkerReply):
    all_predictions: Optional[DataFrame] = None
    prediction: Optional[List[str]] = None
    probabilities: Optional[List[float]] = None
    raw_prediction: Optional[List[float]] = None


class RunModelForDataFrameParam(BaseModel):
    model: ArtifactRef
    dataframe: DataFrame
    target: str
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]


class RunModelParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    inspectionId: int
    project_key: str


class SuiteTestArgument(BaseModel):
    id: int
    testUuid: str
    arguments: Optional[List[FuncArgument]] = None


class TestSuite(WorkerReply):
    is_error: bool
    is_pass: bool
    results: Optional[List[IdentifierSingleTestResult]] = None
    logs: str


class TestSuiteParam(BaseModel):
    tests: Optional[List[SuiteTestArgument]] = None
    globalArguments: Optional[List[FuncArgument]] = None


class PushKind(Enum):
    INVALID = 0
    PERTURBATION = 1
    CONTRIBUTION = 2
    OVERCONFIDENCE = 3
    BORDERLINE = 4


class CallToActionKind(Enum):
    NONE = 0
    CREATE_SLICE = 1
    CREATE_TEST = 2
    CREATE_PERTURBATION = 3
    SAVE_PERTURBATION = 4
    CREATE_ROBUSTNESS_TEST = 5
    CREATE_SLICE_OPEN_DEBUGGER = 6
    OPEN_DEBUGGER_BORDERLINE = 7
    ADD_TEST_TO_CATALOG = 8
    SAVE_EXAMPLE = 9
    OPEN_DEBUGGER_OVERCONFIDENCE = 10
    CREATE_UNIT_TEST = 11


class GetPushParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    dataframe: Optional[DataFrame]
    target: str
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]
    push_kind: Optional[PushKind]
    cta_kind: Optional[CallToActionKind]


class PushDetails(BaseModel):
    action: str
    explanation: str
    button: str
    cta: CallToActionKind


class Push(BaseModel):
    kind: PushKind
    key: Optional[str]
    value: Optional[str]
    push_title: str
    push_details: List[PushDetails]


class PushAction(BaseModel):
    object_uuid: str
    arguments: Optional[List[FuncArgument]]


class GetPushResponse(BaseModel):
    contribution: Optional[Push]
    perturbation: Optional[Push]
    overconfidence: Optional[Push]
    borderline: Optional[Push]
    action: Optional[PushAction]
