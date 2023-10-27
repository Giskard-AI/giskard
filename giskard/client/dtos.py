from typing import Dict, List, Optional

from giskard.core.validation import ConfiguredBaseModel


class TestInputDTO(ConfiguredBaseModel):
    name: str
    value: str
    type: str
    params: List["TestInputDTO"] = list()
    is_alias: bool = False


class SuiteTestDTO(ConfiguredBaseModel):
    testUuid: str
    functionInputs: Dict[str, TestInputDTO]
    displayName: Optional[str] = None


class TestSuiteDTO(ConfiguredBaseModel):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
    function_inputs: List[TestInputDTO]
