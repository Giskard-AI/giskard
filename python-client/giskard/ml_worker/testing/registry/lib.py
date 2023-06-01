from dataclasses import dataclass


@dataclass
class BaseModel:
    name: str


@dataclass
class Dataset:
    name: str
