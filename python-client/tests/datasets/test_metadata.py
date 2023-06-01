import pandas as pd
from unittest import mock
from giskard.datasets import wrap_dataset
from giskard.datasets.metadata import MetadataProviderRegistry, MetadataProvider
from giskard.datasets.metadata.text_metadata_provider import TextMetadataProvider


def test_metadata_registry():
    provider1 = mock.Mock(MetadataProvider)
    provider1.configure_mock(name="provider1")

    MetadataProviderRegistry.register(provider1)

    assert "provider1" in MetadataProviderRegistry.get_available_providers()
    assert MetadataProviderRegistry.get_provider("provider1") == provider1


def test_dataset_metadata_indexer():
    provider = mock.Mock(MetadataProvider)
    provider.configure_mock(name="test_meta")
    provider.generate_metadata.return_value = pd.DataFrame({"test1": [1, 2], "test2": [3, 4]})
    provider.supported_types.return_value = ["text", "category"]

    df = pd.DataFrame({"col1": ["hello", "world"], "col2": ["CAT1", "CAT2"], "col3": [1, 2]})
    dataset = wrap_dataset(df, column_types={"col1": "text", "col2": "category", "col3": "numeric"})

    metadata = dataset.column_meta["col1", "test_meta"]
    assert provider.generate_metadata.is_called_once()

    assert "test1" in metadata.columns
    assert "test2" in metadata.columns
    assert metadata["test1"].tolist() == [1, 2]
    
    # Metadata are cached, no extra calls should be done to the metadata provider
    metadata = dataset.column_meta["col1", "test_meta"]
    assert provider.generate_metadata.is_called_once()
    
    assert "test1" in metadata.columns
    assert "test2" in metadata.columns
    assert metadata["test1"].tolist() == [1, 2]



def test_text_metadata_provider():
    vals = pd.Series(["", "helloo", "world", "helloö world"])

    provider = TextMetadataProvider()
    assert provider.supported_types() == ["text"]

    meta = provider.generate_metadata(vals)

    assert "text_length" in meta.columns
    assert "avg_word_length" in meta.columns
    assert "charset" in meta.columns

    assert meta["text_length"].tolist() == [0, 6, 5, 12]
    assert meta["avg_word_length"].tolist() == [0.0, 6.0, 5.0, 5.5]
    assert meta["charset"].tolist() == ["undefined", "ascii", "ascii", "utf-8"]
