import pandas as pd
from typing import Sequence
from collections import defaultdict

from .registry import MetadataProviderRegistry


class MetadataIndexer:
    """MetadataIndexer allows you to access metadata for a dataset by column and provider name.

    The indexer allows retrieving column metadata as item getters, similarly to in :class:`pandas.DataFrame`.
    The metadata are generated on first access and cached for subsequent requests.

    Example:
        dataset = Dataset(...)
        text_metadata_for_my_column = dataset.column_meta["my_column", "text"]

    """

    _metadata: dict
    _registry = MetadataProviderRegistry

    def __init__(self, dataset):
        self._dataset = dataset
        self._metadata = defaultdict(lambda: pd.DataFrame(index=dataset.df.index))

    def __getitem__(self, key: tuple):
        try:
            column, provider_name = key
        except ValueError:
            raise ValueError("Metadata key must be a tuple of (column, provider_name).")

        if column not in self._dataset.columns:
            raise ValueError(f"Column `{column}` not found in dataset.")

        # Try to return the metadata if it's already been computed
        try:
            return self._metadata[column].loc[:, provider_name]
        except KeyError:
            pass

        # Compute the metadata
        try:
            provider = self._registry.get_provider(provider_name)
        except KeyError:
            raise ValueError(f"Metadata provider `{provider_name}` not found.")

        if self._dataset.column_types[column] not in provider.supported_types():
            raise ValueError(
                f"Metadata provider `{provider_name}` does not support columns of type "
                f"`{self._dataset.column_types[column]}`."
            )

        metadata = provider.generate_metadata(self._dataset.df[column])
        col_index = pd.MultiIndex.from_product([[provider.name], metadata.columns])
        self._metadata[column].loc[:, col_index] = metadata.values

        return self._metadata[column].loc[:, provider_name]

    def available_providers(self) -> Sequence[str]:
        """Returns a list of available metadata providers names."""
        return self._registry.get_available_providers()

    def reset(self) -> None:
        """Resets the metadata cache."""
        self._metadata = defaultdict(pd.DataFrame)

    def has(self, provider_name: str) -> bool:
        """Returns whether the given provider is available."""
        try:
            self._registry.get_provider(provider_name)
            return True
        except KeyError:
            return False


class ColumnMetadataMixin:
    """Decorates a :class:`Dataset` with a `column_meta` property providing a :class:`MetadataIndexer`."""

    @property
    def column_meta(self) -> MetadataIndexer:
        return MetadataIndexer(self)
