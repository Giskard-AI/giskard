from typing import Optional, Callable, Any, Iterable, Dict

import pandas as pd
import pytest
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.embeddings import FakeEmbeddings
from langchain.llms.fake import FakeListLLM
from langchain.text_splitter import CharacterTextSplitter

import giskard
from giskard.core.core import SupportedModelTypes
from giskard.models.langchain import LangchainModel

try:
    from langchain.vectorstores.faiss import FAISS

    found_faiss = True
except ImportError:
    FAISS = None
    found_faiss = False


class FaissRetrieverModel(LangchainModel):
    def __init__(
        self,
        model,
        model_type: SupportedModelTypes,
        retriever: FAISS,
        name: Optional[str] = None,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        **kwargs,
    ):
        self.retriever = retriever

        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            **kwargs,
        )

    def save_artifacts(self, artifact_dir) -> None:
        self.retriever.save_local(artifact_dir)

    @classmethod
    def load_artifacts(cls, local_dir) -> Optional[Dict[str, Any]]:
        from langchain.vectorstores.faiss import FAISS

        embeddings = FakeEmbeddings(size=1352)
        vectorstore = FAISS.load_local(local_dir, embeddings)
        return {"retriever": vectorstore.as_retriever()}


@pytest.mark.skipif(not found_faiss, reason="FAISS not installed.")
def test_vectorstore():
    response = "The president said that she is one of the nation's top legal minds, a former top litigator in private practice, a former federal public defender, and from a family of public school educators and police officers. He also said that she is a consensus builder and has received a broad range of support, from the Fraternal Order of Police to former judges appointed by Democrats and Republicans."
    llm = FakeListLLM(responses=[response])

    loader = TextLoader("./tests/models/langchain/state_of_the_union.txt")
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    embeddings = FakeEmbeddings(size=1352)
    docsearch = FAISS.from_documents(texts, embeddings)

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())

    query = "What did the president say about Ketanji Brown Jackson"

    model = FaissRetrieverModel(
        qa, model_type=SupportedModelTypes.TEXT_GENERATION, retriever=docsearch, feature_names=["query"]
    )
    dataset = giskard.Dataset(pd.DataFrame({"query": [query]}))

    responses = model.predict(dataset)

    assert response == responses.raw[0]

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        model.save(tmpdirname)
        loaded_model = FaissRetrieverModel.load(tmpdirname)

        assert response == loaded_model.predict(dataset).raw[0]
