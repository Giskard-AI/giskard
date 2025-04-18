from unittest.mock import Mock

import numpy as np
import pandas as pd
from bokeh.plotting import figure

from giskard.llm.client.base import ChatMessage
from giskard.rag.knowledge_base import KnowledgeBase


def test_knowledge_base_get_random_documents():
    llm_client = Mock()
    embeddings = Mock()
    embeddings.embed.side_effect = [np.random.rand(5, 10), np.random.rand(3, 10)]

    kb = KnowledgeBase.from_pandas(
        df=pd.DataFrame({"text": ["This is a test string"] * 5}), llm_client=llm_client, embedding_model=embeddings
    )

    # Test when k is smaller than the number of documents
    docs = kb.get_random_documents(3)
    assert len(docs) == 3
    # Check that all document IDs are unique
    assert len(set(doc.id for doc in docs)) == len(docs)

    # Test when k is equal to the number of documents
    docs = kb.get_random_documents(5)
    assert len(docs) == 5
    assert all([doc == kb[doc.id] for doc in docs])

    # Test when k is larger than the number of documents
    docs = kb.get_random_documents(10)
    assert len(docs) == 10
    assert all([doc == kb[doc.id] for doc in docs])


def test_knowledge_base_creation_from_df():
    dimension = 8
    df = pd.DataFrame(["This is a test string"] * 5)

    llm_client = Mock()
    embeddings = Mock()
    random_embedding = np.random.rand(5, dimension)
    embeddings.embed.side_effect = [random_embedding]

    knowledge_base = KnowledgeBase.from_pandas(df, llm_client=llm_client, embedding_model=embeddings)
    assert knowledge_base._index.d == dimension
    assert knowledge_base._embeddings.shape == (5, 8)
    assert len(knowledge_base._documents) == 5
    assert knowledge_base._index.ntotal == 5

    assert np.allclose(knowledge_base._embeddings, random_embedding)


def test_knowledge_base_similarity_search_with_score():
    dimension = 8

    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(100)])

    llm_client = Mock()
    embeddings = Mock()
    embeddings.embed.side_effect = [np.ones((1, dimension)) * 49] + [np.repeat(np.arange(100)[:, None], 8, axis=1)]

    knowledge_base = KnowledgeBase(df, llm_client=llm_client, embedding_model=embeddings)

    query = ["This is test string 50"]
    retrieved_elements = knowledge_base.similarity_search_with_score(query, k=3)
    assert len(retrieved_elements) == 3
    assert retrieved_elements[0][0].content == "This is test string 50"
    assert retrieved_elements[0][1] == 0.0
    assert retrieved_elements[1][0].content == "This is test string 49"
    assert retrieved_elements[1][1] == 8.0
    assert retrieved_elements[2][0].content == "This is test string 51"
    assert retrieved_elements[2][1] == 8.0


def test_knowledge_base_topic_discovery():
    dimension = 2

    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(100)])

    llm_client = Mock()
    embeddings = Mock()

    n = 6
    points = np.exp(2j * np.pi / n * np.random.randint(0, n, 100))
    points = np.stack([points.real, points.imag], axis=1) + np.random.rand(100, dimension) * 0.1
    embeddings.embed.side_effect = [points]

    llm_client.complete = Mock()
    llm_client.complete.side_effect = [ChatMessage(role="assistant", content=f"'Topic {idx+1}'") for idx in range(n)]

    topics = {idx: f"'Topic {idx+1}'" for idx in range(n)}
    topics[-1] = "Others"
    knowledge_base = KnowledgeBase(df, llm_client=llm_client, embedding_model=embeddings)
    assert len(knowledge_base.topics) == n + 1
    assert knowledge_base.topics == topics


def test_knowledge_base_topic_plot():
    dimension = 2

    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(100)])

    llm_client = Mock()
    embeddings = Mock()

    n = 6
    points = np.exp(2j * np.pi / n * np.random.randint(0, n, 100))
    points = np.stack([points.real, points.imag], axis=1) + np.random.rand(100, dimension) * 0.2
    embeddings.embed.side_effect = [points]

    llm_client.complete = Mock()
    llm_client.complete.side_effect = [ChatMessage(role="assistant", content=f"'Topic {idx+1}'") for idx in range(n)]

    knowledge_base = KnowledgeBase(df, llm_client=llm_client, embedding_model=embeddings)
    plot = knowledge_base.get_knowledge_plot()
    assert plot is not None
    assert isinstance(plot, figure)


def test_knowledge_base_basic_properties():
    llm_client = Mock()
    embeddings = Mock()
    embeddings.embed.side_effect = [np.random.rand(5, 10), np.random.rand(3, 10)]

    # Length
    kb = KnowledgeBase.from_pandas(
        df=pd.DataFrame({"text": ["This is a test string"] * 5}), llm_client=llm_client, embedding_model=embeddings
    )
    assert len(kb) == 5

    kb = KnowledgeBase.from_pandas(
        df=pd.DataFrame({"text": ["Test 1", "Test 2", "Test 3"]}), llm_client=llm_client, embedding_model=embeddings
    )
    assert len(kb) == 3


def test_knowledge_base_save_and_load(tmp_path):
    class PickeableMock(Mock):
        model = "test-model"

        def __reduce__(self):
            return (Mock, ())

    dim = 8
    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(10)])

    llm_client = PickeableMock()
    embeddings = PickeableMock()
    embeddings.embed = Mock()
    random_embedding = np.random.rand(10, dim)
    embeddings.embed.side_effect = [random_embedding[i] for i in range(random_embedding.shape[0])]

    # Create and save the knowledge base
    knowledge_base = KnowledgeBase.from_pandas(df, llm_client=llm_client, embedding_model=embeddings)
    save_path = tmp_path / "knowledge_base.pkl"
    knowledge_base._embeddings  # generate embeddings
    knowledge_base.save(save_path)

    # Load the knowledge base
    loaded_knowledge_base = KnowledgeBase.load(save_path)

    # Verify the loaded knowledge base
    assert len(loaded_knowledge_base) == len(knowledge_base)
    assert np.allclose(loaded_knowledge_base._embeddings, knowledge_base._embeddings)
    assert loaded_knowledge_base._knowledge_base_df.equals(knowledge_base._knowledge_base_df)


def test_knowledge_base_push_to_hf_hub(mocker):
    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(10)])
    llm_client = Mock()
    embeddings = Mock()
    embeddings.embed.side_effect = [np.random.rand(10, 8)]

    knowledge_base = KnowledgeBase.from_pandas(df, llm_client=llm_client, embedding_model=embeddings)

    mock_create_repo = mocker.patch("huggingface_hub.HfApi.create_repo")
    mock_upload_file = mocker.patch("huggingface_hub.upload_file")

    knowledge_base.push_to_hf_hub(repo_id="test-repo", hf_token="fake-token", private=True)

    mock_create_repo.assert_called_once_with("test-repo", repo_type="dataset", private=True, exist_ok=True)
    mock_upload_file.assert_called()


def test_knowledge_base_load_from_hf_hub(mocker):
    mock_hf_hub_download = mocker.patch("huggingface_hub.hf_hub_download")
    mock_hf_hub_download.side_effect = [
        "/mock/path/knowledge_base.parquet",
        "/mock/path/embeddings.npy",
        "/mock/path/reduced_embeddings.npy",
        "/mock/path/config.json",
        "/mock/path/llm_client.pkl",
        "/mock/path/embedding_model.pkl",
    ]

    mock_load_parquet = mocker.patch("pandas.read_parquet")
    mock_load_parquet.return_value = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(10)])

    mock_load_pickle = mocker.patch("pickle.load")
    mock_load_pickle.side_effect = [Mock(), Mock()]

    knowledge_base = KnowledgeBase.load_from_hf_hub(repo_id="test-repo", hf_token="fake-token")

    assert len(knowledge_base) == 10
    mock_hf_hub_download.assert_any_call(repo_id="test-repo", filename="knowledge_base.parquet", token="fake-token")
    mock_load_parquet.assert_called_once()
    mock_load_pickle.assert_called()
