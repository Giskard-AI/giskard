from unittest import mock

import pandas as pd

from giskard.datasets import Dataset
from giskard.datasets.metadata import MetadataProviderRegistry, MetadataProvider
from giskard.datasets.metadata.indexing import ColumnMetadataMixin, MetadataIndexer
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

    MetadataProviderRegistry.register(provider)

    df = pd.DataFrame({"col1": ["hello", "world"], "col2": ["CAT1", "CAT2"], "col3": [1, 2]})
    dataset = Dataset(df, column_types={"col1": "text", "col2": "category", "col3": "numeric"})

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


def test_column_metadata_mixin():
    class Demo(ColumnMetadataMixin):
        def __init__(self, df):
            self.df = df

    demo = Demo(pd.DataFrame({"text_feature": ["one", "two"]}))

    assert isinstance(demo.column_meta, MetadataIndexer)

    # Result should be cached
    instance1 = demo.column_meta
    instance2 = demo.column_meta

    assert id(instance1) == id(instance2)


def test_text_metadata_provider():
    vals = pd.Series(
        [
            "",
            "helloo",
            "world",
            "helloö world",
            "Например, прошлым летом я начал заниматься " "кайт-серфингом- новые занятия, одним словом.",
        ]
    )

    provider = TextMetadataProvider()
    assert provider.supported_types() == ["text"]

    meta = provider.generate_metadata(vals)

    assert "text_length" in meta.columns
    assert "avg_word_length" in meta.columns
    assert "charset" in meta.columns

    assert meta["text_length"].tolist() == [0, 6, 5, 12, 87]
    assert meta["avg_word_length"].tolist() == [0.0, 6.0, 5.0, 5.5, 7]
    assert meta["charset"].tolist() == ["undefined", "ascii", "ascii", "utf-8", "utf-8"]
    assert meta["language"].tolist() == [pd.NA, pd.NA, pd.NA, pd.NA, "ru"]


def test_lang_detected_proportion():
    vals = pd.Series(
        [
            "IA signifie Intelligence Artificielle.",
            "Malgré son intelligence, il est toujours réticent à donner son point de vue.",
            "Benson et Holmes ont analysé les effets psychologiques de l'insémination artificielle chez les parents.",
            "N'insulte pas mon intelligence.",
            "Chaque avancée dans la civilisation a été dénoncée car artificielle tandis qu'elle était récente.",
            "Son intelligence me surprend souvent.",
            "Autrefois langue artificielle rejetée, l'espéranto a gagné le respect d'une nouvelle génération de "
            "linguistes, en tant que langue construite ayant remporté le plus de succès de tous les temps.",
            "Il y a aussi un type d'idéalisme qui dit que même sans force ou sans intelligence, on peut faire n'importe "
            "quoi si on persiste.",
            "Il réanima l'enfant par respiration artificielle.",
            "Ton intelligence est aussi grande que la distance entre Bombay et Mumbai.",
            "L'intelligence artificielle ne peut pas battre la stupidité naturelle.",
            "Son intelligence et son expérience lui permirent de régler le souci.",
            "Certains secteurs soutenaient la création dans l'espace de structures géantes pour le logement, dotées de "
            "gravitation artificielle.",
            "N'insultez pas mon intelligence.",
            "AI stands for artificial intelligence.",
            "For all his cleverness, he is always reluctant to give his views.",
            "Benson and Holmes analyzed the psychological effect of artificial insemination on parents.",
            "Don't insult my intelligence.",
            "Every advance in civilization has been denounced as unnatural while it was recent.",
            "Her cleverness often amazes me.",
            "Once dismissed as an artificial language, Esperanto has gained the respect of a new generation of "
            "linguists, as the most successful planned language of all time.",
            "There is also one type of idealism that says even without strength or intelligence you can do anything if "
            "you can merely persist.",
            "He revived the child with artificial respiration.",
            "Your intelligence is as vast as the distance between Bombay and Mumbai.",
            "Artificial intelligence cannot beat natural stupidity.",
            "His intelligence and experience enabled him to deal with the trouble.",
            "Certain industries advocated creating megastructures in space for habitation with artificial gravity.",
            "Don't insult my intelligence.",
        ]
    )

    provider = TextMetadataProvider()
    assert provider.supported_types() == ["text"]

    meta = provider.generate_metadata(vals)
    language_counts = meta["language"].value_counts()

    assert language_counts["fr"] == 10
    assert language_counts["en"] == 10
    assert meta["language"].isna().sum() == 8
