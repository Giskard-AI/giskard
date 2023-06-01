from typing import List, Dict, Optional

from pydantic import Model


class TestInputDTO(Model):
    name: str
    value: str
    is_alias: bool = False


class SuiteTestDTO(Model):
    testId: str
    testInputs: Dict[str, TestInputDTO]


class TestSuiteNewDTO(Model):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
