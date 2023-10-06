import pandas as pd
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.embeddings import FakeEmbeddings
from langchain.llms.fake import FakeListLLM
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS

import giskard
from giskard.models.langchain import LangchainModel


def test_vectorstore():
    response = "The president said that she is one of the nation's top legal minds, a former top litigator in private practice, a former federal public defender, and from a family of public school educators and police officers. He also said that she is a consensus builder and has received a broad range of support, from the Fraternal Order of Police to former judges appointed by Democrats and Republicans."
    responses = [response]
    llm = FakeListLLM(responses=responses)

    loader = TextLoader("./tests/models/langchain/state_of_the_union.txt")
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    embeddings = FakeEmbeddings(size=1352)
    docsearch = FAISS.from_documents(texts, embeddings)

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())

    query = "What did the president say about Ketanji Brown Jackson"

    def save_local(persist_directory):
        docsearch.save_local(persist_directory)

    def load_retriever(persist_directory):
        embeddings = FakeEmbeddings(size=1352)
        vectorstore = FAISS.load_local(persist_directory, embeddings)
        return vectorstore.as_retriever()

    model = giskard.Model(qa, model_type="text_generation", save_db=save_local, loader_fn=load_retriever,
                          feature_names=['query'])
    dataset = giskard.Dataset(pd.DataFrame({'query': [query]}))

    responses = model.predict(dataset)

    assert qa.run(query) == responses.raw[0]

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        model.save(tmpdirname)
        loaded_model = LangchainModel.load(tmpdirname)

        assert qa.run(query) == loaded_model.predict(dataset).raw[0]
