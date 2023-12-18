from typing import Tuple

from pathlib import Path

import pandas as pd

from giskard import Dataset, Model

IPCC_REPORT_URL = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_LongerReport.pdf"

LLM_NAME = "gpt-3.5-turbo-instruct"

TEXT_COLUMN_NAME = "query"

PROMPT_TEMPLATE = """You are the Climate Assistant, a helpful AI assistant made by Giskard.
Your task is to answer common questions on climate change.
You will be given a question and relevant excerpts from the IPCC Climate Change Synthesis Report (2023).
Please provide short and clear answers based on the provided context. Be polite and helpful.

Context:
{context}

Question:
{question}

Your answer:
"""


def ippc_model_and_dataset() -> Tuple[Model, Dataset]:
    from langchain import FAISS, OpenAI, PromptTemplate
    from langchain.chains import RetrievalQA, load_chain
    from langchain.chains.base import Chain
    from langchain.document_loaders import PyPDFLoader
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Define a custom Giskard model wrapper for the serialization.
    class FAISSRAGModel(Model):
        def model_predict(self, df: pd.DataFrame) -> pd.DataFrame:
            return df[TEXT_COLUMN_NAME].apply(lambda x: self.model.run({"query": x}))

        def save_model(self, path: str, *args, **kwargs):
            out_dest = Path(path)
            # Save the chain object
            self.model.save(out_dest.joinpath("model.json"))

            # Save the FAISS-based retriever
            db = self.model.retriever.vectorstore
            db.save_local(out_dest.joinpath("faiss"))

        @classmethod
        def load_model(cls, path: str, *args, **kwargs) -> Chain:
            src = Path(path)

            # Load the FAISS-based retriever
            db = FAISS.load_local(src.joinpath("faiss"), OpenAIEmbeddings())

            # Load the chain, passing the retriever
            chain = load_chain(src.joinpath("model.json"), retriever=db.as_retriever())
            return chain

    def get_context_storage() -> FAISS:
        """Initialize a vector storage of embedded IPCC report chunks (context)."""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100, add_start_index=True)
        docs = PyPDFLoader(IPCC_REPORT_URL).load_and_split(text_splitter)
        db = FAISS.from_documents(docs, OpenAIEmbeddings())
        return db

    # Create the chain.
    llm = OpenAI(model=LLM_NAME, temperature=0)
    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["question", "context"])
    climate_qa_chain = RetrievalQA.from_llm(llm=llm, retriever=get_context_storage().as_retriever(), prompt=prompt)

    # Wrap the QA chain
    giskard_model = FAISSRAGModel(
        model=climate_qa_chain,  # A prediction function that encapsulates all the data pre-processing steps and that could be executed with the dataset used by the scan.
        model_type="text_generation",  # Either regression, classification or text_generation.
        name="Climate Change Question Answering",  # Optional.
        description="This model answers any question about climate change based on IPCC reports",  # Is used to generate prompts during the scan.
        feature_names=[TEXT_COLUMN_NAME],  # Default: all columns of your dataset.
    )

    # Optional: Wrap a dataframe of sample input prompts to validate the model wrapping and to narrow specific tests' queries.
    giskard_dataset = Dataset(
        pd.DataFrame(
            {
                TEXT_COLUMN_NAME: [
                    "According to the IPCC report, what are key risks in the Europe?",
                    "Is sea level rise avoidable? When will it stop?",
                ]
            }
        ),
        target=None,
    )
    return giskard_model, giskard_dataset
