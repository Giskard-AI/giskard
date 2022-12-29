from typing import List

from pydantic import BaseModel


class TestParameterDTO(BaseModel):
    name: str
    value: str


class SuiteTestDTO(BaseModel):
    testId: str
    parameters: List[TestParameterDTO]


class TestSuiteNewDTO(BaseModel):
    name: str
    project_key: str
    tests: List[SuiteTestDTO]
