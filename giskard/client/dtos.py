from typing import List, Dict, Optional

from pydantic import BaseModel


class TestInputDTO(BaseModel):
    name: str
    value: str
    type: str
    params: List["TestInputDTO"] = list()
    is_alias: bool = False


class SuiteTestDTO(BaseModel):
    testUuid: str
    functionInputs: Dict[str, TestInputDTO]


class TestSuiteDTO(BaseModel):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
