from typing import List, Dict, Optional

from pydantic import BaseModel


class TestInputDTO(BaseModel):
    name: str
    value: str
    is_alias: bool = False


class SuiteTestDTO(BaseModel):
    testUuid: str
    testInputs: Dict[str, TestInputDTO]


class TestSuiteNewDTO(BaseModel):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
