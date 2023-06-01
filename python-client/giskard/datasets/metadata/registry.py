from abc import ABC, abstractmethod
import pandas as pd
from typing import Sequence

from ...core.core import ColumnType


class MetadataProvider(ABC):
    name: str

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def generate_metadata(self, values: pd.Series) -> pd.DataFrame:
        ...

    @abstractmethod
    def supported_types(self) -> Sequence[ColumnType]:
        ...


class MetadataProviderRegistry:
    _provider = dict()

    @classmethod
    def register(cls, provider):
        cls._provider[provider.name] = provider

    @classmethod
    def get_provider(cls, name) -> MetadataProvider:
        return cls._provider[name]

    @classmethod
    def get_available_providers(cls) -> Sequence[str]:
        return list(cls._provider.keys())
