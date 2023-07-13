from typing import Dict, List
from enum import Enum

from pydantic import BaseModel


class Empty(BaseModel):
    pass


class ArtifactRef(BaseModel):
    project_key: str
    id: str
    sample: bool


class TestFunctionArgument(BaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


class FunctionMeta(BaseModel):
    uuid: str
    name: str
    displayName: str
    version: int
    module: str
    doc: str
    moduleDoc: str
    args: List[TestFunctionArgument]
    tags: List[str]
    code: str
    type: str


class DatasetProcessFuctionMeta(BaseModel):
    uuid: str
    name: str
    displayName: str
    version: int
    module: str
    doc: str
    moduleDoc: str
    args: List[TestFunctionArgument]
    tags: List[str]
    code: str
    type: str
    cellLevel: bool
    columnType: str
    processType: str


class Catalog(BaseModel):
    tests: Dict[str, FunctionMeta]
    slices: Dict[str, DatasetProcessFuctionMeta]
    transformations: Dict[str, DatasetProcessFuctionMeta]


class DataRow(BaseModel):
    columns: Dict[str, str]


class DataFrame(BaseModel):
    rows: List[DataRow]


class DatasetRowModificationResult(BaseModel):
    rowId: int
    modifications: Dict[str, str]


class DatasetProcessing(BaseModel):
    datasetId: str
    totalRows: int
    filteredRows: List[int]
    modifications: List[DatasetRowModificationResult]


class FuncArgument(BaseModel):
    name: str
    model: ArtifactRef
    dataset: ArtifactRef
    float: float
    int: int
    str: str
    bool: bool
    slicingFunction: ArtifactRef
    transformationFunction: ArtifactRef
    kwargs: str
    args: List["FuncArgument"]
    none: bool


class DatasetProcessingFunction(BaseModel):
    slicingFunction: ArtifactRef
    transformationFunction: ArtifactRef
    arguments: List[FuncArgument]


class DatesetProcessingParam(BaseModel):
    dataset: ArtifactRef
    functions: List[DatasetProcessingFunction]


class EchoMsg(BaseModel):
    msg: str


class Explanation(BaseModel):
    per_feature: Dict[str, float]


class Explain(BaseModel):
    explanations: Dict[str, Explanation]


class ExplainParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    columns: Dict[str, str]


class WeightsPerFeature(BaseModel):
    weights: List[float]


class ExplainText(BaseModel):
    words: List[str]
    weights: Dict[str, WeightsPerFeature]


class ExplainTextParam(BaseModel):
    model: ArtifactRef
    feature_name: str
    columns: Dict[str, str]
    column_types: Dict[str, str]
    n_samples: int


class GeneratedTestInput(BaseModel):
    name: str
    value: str
    is_alias: bool


class GeneratedTestSuite(BaseModel):
    test_uuid: str
    inputs: List[GeneratedTestInput]


class GenerateTestSuite(BaseModel):
    tests: List[GeneratedTestSuite]


class ModelMeta(BaseModel):
    model_type: str


class DatasetMeta(BaseModel):
    target: str


class SuiteInput(BaseModel):
    name: str
    type: str
    modelMeta: ModelMeta
    datasetMeta: DatasetMeta


class GenerateTestSuiteParam(BaseModel):
    project_key: str
    inputs: List[SuiteInput]


class Platform(BaseModel):
    machine: str
    node: str
    processor: str
    release: str
    system: str
    version: str


class GetInfo(BaseModel):
    platform: Platform
    interpreter: str
    interpreterVersion: str
    installedPackages: Dict[str, str]
    internalGrpcAddress: str
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
    value: List[int]
    count: int


class SingleTestResult(BaseModel):
    passed: bool
    is_error: bool
    messages: List[TestMessage]
    props: Dict[str, str]
    metric: float
    missing_count: int
    missing_percent: float
    unexpected_count: int
    unexpected_percent: float
    unexpected_percent_total: float
    unexpected_percent_nonmissing: float
    partial_unexpected_index_list: List[int]
    partial_unexpected_counts: List[PartialUnexpectedCounts]
    unexpected_index_list: List[int]
    outputDf: bytes
    number_of_perturbed_rows: int
    actual_slices_size: List[int]
    reference_slices_size: List[int]


class IdentifierSingleTestResult(BaseModel):
    id: int
    result: SingleTestResult


class NamedSingleTestResult(BaseModel):
    testUuid: str
    result: SingleTestResult


class RunAdHocTest(BaseModel):
    results: List[NamedSingleTestResult]


class RunAdHocTestParam(BaseModel):
    testUuid: str
    arguments: List[FuncArgument]


class RunModelForDataFram(BaseModel):
    all_predictions: DataFrame
    prediction: List[str]
    probabilities: List[float]
    raw_prediction: List[float]


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
    arguments: List[FuncArgument]


class TestFunctionArgument(BaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


class TestSuite(BaseModel):
    is_error: bool
    is_pass: bool
    results: IdentifierSingleTestResult
    logs: str


class TestSuiteParam(BaseModel):
    tests: List[SuiteTestArgument]
    globalArguments: List[FuncArgument]
