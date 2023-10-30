from typing import Dict, List, Optional, Type

import json
from pathlib import Path

import pydantic
import pytest
from packaging import version
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

import giskard
import giskard.ml_worker.websocket
from giskard.core.validation import ConfiguredBaseModel

IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")
if IS_PYDANTIC_V2:
    from pydantic.fields import FieldInfo as ModelField
else:
    from pydantic.fields import ModelField

FILTERED_CLASSES = [BaseModel, ConfiguredBaseModel]

MANDATORY_FIELDS = {
    "ArtifactRef": ["id"],
    "Catalog": ["tests", "slices", "transformations"],
    "DataFrame": ["rows"],
    "DataRow": ["columns"],
    "DatasetMeta": [],
    "DatasetProcessFunctionMeta": ["uuid", "name", "code", "version", "cellLevel"],
    "DatasetProcessing": ["datasetId", "totalRows"],
    "DatasetProcessingFunction": [],
    "DatasetProcessingParam": ["dataset"],
    "DatasetRowModificationResult": ["rowId", "modifications"],
    "EchoMsg": ["msg"],
    "Empty": [],
    "ErrorReply": ["error_str", "error_type"],
    "Explain": ["explanations"],
    "ExplainParam": ["model", "dataset", "columns"],
    "ExplainText": ["weights"],
    "ExplainTextParam": ["model", "feature_name", "columns", "column_types"],
    "Explanation": ["per_feature"],
    "FuncArgument": ["name", "none"],
    "FunctionMeta": ["uuid", "name", "code", "version"],
    "GenerateTestSuite": [],
    "GenerateTestSuiteParam": ["project_key"],
    "GeneratedTestInput": ["name", "value", "is_alias"],
    "GeneratedTestSuite": ["test_uuid"],
    "GetInfo": [
        "platform",
        "interpreter",
        "interpreterVersion",
        "installedPackages",
        "mlWorkerId",
        "isRemote",
        "pid",
        "processStartTime",
        "giskardClientVersion",
    ],
    "GetInfoParam": ["list_packages"],
    "GetPushParam": ["model", "dataset", "column_types", "column_dtypes", "rowIdx"],
    "GetPushResponse": [],
    "IdentifierSingleTestResult": ["id", "result"],
    "ModelMeta": [],
    "NamedSingleTestResult": ["testUuid", "result"],
    "PartialUnexpectedCounts": ["count"],
    "Platform": ["machine", "node", "processor", "release", "system", "version"],
    "Push": ["kind", "push_title", "push_details"],
    "PushAction": ["object_uuid"],
    "PushDetails": ["action", "explanation", "button", "cta"],
    "RunAdHocTest": [],
    "RunAdHocTestParam": ["testUuid"],
    "RunModelForDataFrame": [],
    "RunModelForDataFrameParam": ["model", "dataframe", "column_types", "column_dtypes"],
    "RunModelParam": ["model", "dataset", "inspectionId", "project_key"],
    "SingleTestResult": ["passed"],
    "SuiteInput": ["name", "type"],
    "SuiteTestArgument": ["id", "testUuid"],
    "TestFunctionArgument": ["name", "type", "optional", "default", "argOrder"],
    "TestMessage": ["type", "text"],
    "TestSuite": ["is_error", "is_pass", "logs"],
    "TestSuiteParam": [],
    "WeightsPerFeature": [],
    "WorkerReply": [],
}

OPTIONAL_FIELDS = {
    "ArtifactRef": ["project_key", "sample"],
    "Catalog": [],
    "DataFrame": [],
    "DataRow": [],
    "DatasetMeta": ["target"],
    "DatasetProcessFunctionMeta": [
        "displayName",
        "module",
        "doc",
        "moduleDoc",
        "args",
        "tags",
        "type",
        "columnType",
        "processType",
    ],
    "DatasetProcessing": ["filteredRows", "modifications"],
    "DatasetProcessingFunction": ["slicingFunction", "transformationFunction", "arguments"],
    "DatasetProcessingParam": ["functions"],
    "DatasetRowModificationResult": [],
    "EchoMsg": [],
    "Empty": [],
    "ErrorReply": ["detail"],
    "Explain": [],
    "ExplainParam": [],
    "ExplainText": ["words"],
    "ExplainTextParam": [],
    "Explanation": [],
    "FuncArgument": [
        "model",
        "dataset",
        "float",
        "int",
        "str",
        "bool",
        "slicingFunction",
        "transformationFunction",
        "kwargs",
        "args",
    ],
    "FunctionMeta": [
        "displayName",
        "module",
        "doc",
        "moduleDoc",
        "args",
        "tags",
        "type",
        "debugDescription",
    ],
    "GenerateTestSuite": ["tests"],
    "GenerateTestSuiteParam": ["inputs"],
    "GeneratedTestInput": [],
    "GeneratedTestSuite": ["inputs"],
    "GetInfo": [],
    "GetInfoParam": [],
    "GetPushParam": ["dataframe", "target", "push_kind", "cta_kind"],
    "GetPushResponse": ["contribution", "perturbation", "overconfidence", "borderline", "action"],
    "IdentifierSingleTestResult": ["arguments"],
    "ModelMeta": ["model_type"],
    "NamedSingleTestResult": [],
    "PartialUnexpectedCounts": ["value"],
    "Platform": [],
    "Push": ["key", "value"],
    "PushAction": ["arguments"],
    "PushDetails": [],
    "RunAdHocTest": ["results"],
    "RunAdHocTestParam": ["arguments", "debug"],
    "RunModelForDataFrame": ["all_predictions", "prediction", "probabilities", "raw_prediction"],
    "RunModelForDataFrameParam": ["target"],
    "RunModelParam": [],
    "SingleTestResult": [
        "is_error",
        "messages",
        "props",
        "metric",
        "missing_count",
        "missing_percent",
        "unexpected_count",
        "unexpected_percent",
        "unexpected_percent_total",
        "unexpected_percent_nonmissing",
        "partial_unexpected_index_list",
        "partial_unexpected_counts",
        "unexpected_index_list",
        "output_df",
        "number_of_perturbed_rows",
        "actual_slices_size",
        "reference_slices_size",
        "output_df_id",
    ],
    "SuiteInput": ["modelMeta", "datasetMeta"],
    "SuiteTestArgument": ["arguments"],
    "TestFunctionArgument": [],
    "TestMessage": [],
    "TestSuite": ["results"],
    "TestSuiteParam": ["tests", "globalArguments"],
    "WeightsPerFeature": ["weights"],
    "WorkerReply": [],
}
ALIASED_FIELDS = {
    "FuncArgument": {"float_arg": "float", "int_arg": "int", "str_arg": "str", "bool_arg": "bool", "is_none": "none"}
}


def get_all_dto_classes() -> List[Type[BaseModel]]:
    klasses: List[Type[BaseModel]] = []
    for name in dir(giskard.ml_worker.websocket):
        maybe_klass = getattr(giskard.ml_worker.websocket, name)
        if isinstance(maybe_klass, type) and issubclass(maybe_klass, BaseModel) and maybe_klass not in FILTERED_CLASSES:
            klasses.append(maybe_klass)

    return klasses


def get_fields(klass: Type[BaseModel]) -> Dict[str, ModelField]:
    if IS_PYDANTIC_V2:
        return klass.model_fields
    return klass.__fields__


def get_name(name: str, field: ModelField) -> str:
    return field.alias if field.alias is not None else name


def get_alias(field: ModelField) -> Optional[str]:
    if IS_PYDANTIC_V2:
        return field.alias
    return field.alias if field.has_alias else None


def is_required(field: ModelField) -> bool:
    if IS_PYDANTIC_V2:
        return field.is_required()
    return field.required


ALL_DTOS = [pytest.param((klass), id=klass.__name__) for klass in get_all_dto_classes()]


# Goal is to ensure every DTO is tested properly
def test_all_dtos_are_configured():
    missing_classes: List[Type[BaseModel]] = []
    for param_set in ALL_DTOS:
        klass = param_set.values[0]
        if not issubclass(klass, ConfiguredBaseModel):
            missing_classes.append(klass)
    output = "\n  -".join([elt.__qualname__ for elt in missing_classes])
    if len(missing_classes) > 0:
        raise ValueError(f"All dtos should use ConfiguredBaseModel as base class, one not using are :\n  -{output}")


# Goal is to ensure every DTO is tested properly
def test_list_mandatory_all_classes():
    missing_classes: List[Type[BaseModel]] = []
    for param_set in ALL_DTOS:
        klass = param_set.values[0]
        if klass.__name__ not in MANDATORY_FIELDS.keys():
            missing_classes.append(klass)
    output = "\n  -".join([elt.__qualname__ for elt in missing_classes])
    if len(missing_classes) > 0:
        raise ValueError(f"All dtos should be tested here, missing ones are :\n  -{output}")


def test_list_optional_all_classes():
    missing_classes: List[Type[BaseModel]] = []
    for param_set in ALL_DTOS:
        klass = param_set.values[0]
        if klass.__name__ not in OPTIONAL_FIELDS.keys():
            missing_classes.append(klass)
    output = "\n  -".join([elt.__qualname__ for elt in missing_classes])
    if len(missing_classes) > 0:
        raise ValueError(f"All dtos should be tested here, missing ones are :\n  -{output}")


# Goal is to ensure that no fields is becoming mandatory by error
@pytest.mark.parametrize("klass", ALL_DTOS)
def test_dto_ensure_all_mandatory_values(klass: Type[BaseModel]):
    # Here we ensure all mandatory keys are present in dto_mandatory
    mandatory_field_names = [get_name(name, field) for name, field in get_fields(klass).items() if is_required(field)]
    assert set(mandatory_field_names) == set(MANDATORY_FIELDS.get(klass.__name__, []))


# Goal is to ensure that no fields is becoming optional by error
@pytest.mark.parametrize("klass", ALL_DTOS)
def test_dto_ensure_all_optional_values(klass: Type[BaseModel]):
    # Here we ensure all optional keys are present in dto_mandatory
    mandatory_field_names = [
        get_name(name, field) for name, field in get_fields(klass).items() if not is_required(field)
    ]
    assert set(mandatory_field_names) == set(OPTIONAL_FIELDS.get(klass.__name__, []))


# Goal is to ensure that no alias has been changed by error
@pytest.mark.parametrize("klass", ALL_DTOS)
def test_dto_verify_mapping(klass: Type[BaseModel]):
    # Here we ensure all optional keys are present in dto_mandatory
    mapping_dto = ALIASED_FIELDS.get(klass.__name__, {})
    aliased_fields = []
    attr_name_aliased = []

    for name, field in get_fields(klass).items():
        if get_alias(field) is not None:
            aliased_fields.append(field.alias)
            attr_name_aliased.append(name)
            assert mapping_dto.get(name) == field.alias
    # Ensure no alias have been removed or created by error
    assert set(aliased_fields) == set(mapping_dto.values())
    assert set(attr_name_aliased) == set(mapping_dto.keys())


@pytest.mark.parametrize("klass", ALL_DTOS)
def test_serialisation_dtos(klass: BaseModel):
    fixtures_dir = Path(__file__).parent / "fixtures"
    with (fixtures_dir / "with_alias.json").open("r", encoding="utf-8") as fp:
        all_datas = json.load(fp)
        for instance_dict in all_datas[klass.__name__]:
            # Should not fail
            instance = klass(**instance_dict)
            assert json.loads(instance.json(by_alias=True)) == instance_dict


def print_all_mapping():
    res = {}
    for param_set in ALL_DTOS:
        dto = param_set.values[0]
        mandatory_field_names = {
            name: get_alias(field) for name, field in get_fields(dto).items() if get_alias(field) is not None
        }
        if len(mandatory_field_names) > 0:
            res[dto.__name__] = mandatory_field_names
    print(res)


def print_all_mandatory_values():
    res = {}
    for param_set in ALL_DTOS:
        dto = param_set.values[0]
        mandatory_field_names = [get_name(name, field) for name, field in get_fields(dto).items() if is_required(field)]
        res[dto.__name__] = mandatory_field_names
    print(res)


def print_all_optional_values():
    res = {}
    for param_set in ALL_DTOS:
        dto = param_set.values[0]
        mandatory_field_names = [
            get_name(name, field) for name, field in get_fields(dto).items() if not is_required(field)
        ]
        res[dto.__name__] = mandatory_field_names
    print(res)


class CustomFactory(ModelFactory):
    __allow_none_optionals__ = False
    __is_base_factory__ = True
    __randomize_collection_length__ = True
    __min_collection_length__ = 0
    __max_collection_length__ = 1


def pydantic_factory(klass: Type[BaseModel]):
    factory = CustomFactory.create_factory(model=klass)
    factory.__base_factory_overrides__ = {BaseModel: CustomFactory}

    return factory


def generate_serialisation_data():
    all_snapshots = {}
    for param_set in ALL_DTOS:
        dto = param_set.values[0]
        factory = pydantic_factory(dto)
        factory.seed_random(1)
        all_snapshots[dto.__name__] = factory.batch(3)

    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    with (fixtures_dir / "with_alias.json").open("w", encoding="utf-8") as fp:
        json.dump(
            {k: [json.loads(elt.json(by_alias=True)) for elt in v] for k, v in all_snapshots.items()},
            fp,
            allow_nan=False,
            indent=2,
        )


if __name__ == "__main__":
    print_all_mandatory_values()
    print_all_optional_values()
    print_all_mapping()
    generate_serialisation_data()
