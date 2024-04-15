# %% Import necessary libraries
# Importing the classes and functions needed for document loading, text splitting, and setting up embeddings.

from langchain import PromptTemplate
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
import pandas as pd
import giskard as gsk
from pathlib import Path
from langchain.chains import load_chain
import logging
from openai import OpenAI
from giskard.llm.client.openai import OpenAIClient
from giskard.llm.client.mistral import MistralClient

# %% Load and split the document
# Loading a PDF document from a URL using PyPDFLoader.
# Splitting the document text into manageable chunks using RecursiveCharacterTextSplitter.

loader = PyPDFLoader("https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_LongerReport.pdf")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100, length_function=len, add_start_index=True)
docs = loader.load_and_split(text_splitter)

# %% Create an embedding database
# Creating an embedding database using FAISS from the split documents.
# Using OpenAIEmbeddings to convert text data into embeddings.

db = FAISS.from_documents(docs, OpenAIEmbeddings())

# %% Setup the retrieval-based QA system
# Setting up a retrieval-based QA system using the RetrievalQA class.
# Configuring the language model and the prompt template for answering questions.

PROMPT_TEMPLATE = """
You are the Climate Assistant, an helpful AI assistant made by Giskard. Your task is to answer common questions on climate change.
You will be given a question and relevant excerpts from the IPCC Climate Change Synthesis Report (2023). Please provide short and clear answers based on the provided context.
Be polite and helpful.

Context:
{context}

Question:
{question}

Your answer:
"""

llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)
retriever = db.as_retriever()
chain = RetrievalQA.from_llm(
    llm=llm,
    retriever=retriever,
    prompt=PromptTemplate(
        template=PROMPT_TEMPLATE, input_variables=["question", "context"]
    ),
)

# %% Test the QA system
# Testing the retrieval-based QA system by asking a specific question about climate change.

result = chain("Is sea level rise avoidable? When will it stop?")
print(result)

# %% Define and use a Giskard model
# Defining a custom model class in Giskard for running queries and handling model storage.

class RAGModel(gsk.Model):
    def model_predict(self, df: pd.DataFrame):
        return df["question"].apply(lambda x: self.model.run({"query": x}))

    def save_model(self, path: str):
        out_dest = Path(path)
        self.model.save(out_dest.joinpath("model.json"))
        chain.retriever.vectorstore.save_local(out_dest.joinpath("faiss"))

    @classmethod
    def load_model(cls, path: str):
        src = Path(path)
        db = FAISS.load_local(src.joinpath("faiss"), OpenAIEmbeddings())
        chain = load_chain(src.joinpath("model.json"), retriever=db.as_retriever())
        return chain

# %% Setup dataset and model
# Setting up a DataFrame with sample questions and creating a dataset for model testing.

df = pd.DataFrame({
    "question": [
        "According to the IPCC report, what are key risks in Europe?",
        "Is sea level rise avoidable? When will it stop?",
    ]
})
dataset = gsk.Dataset(df, column_types={"question": "text"})
model = RAGModel(chain, model_type="text_generation", name="Climate Test", description="This model summarizes questions about climate change based on IPCC reports.")

# %% Configure and run scans
# Configuring logging and LLM model for use in Giskard scans.
# Running a scan on the model and dataset to evaluate various aspects.

logging.getLogger("giskard.llm").setLevel(logging.DEBUG)
gsk.llm.set_llm_api("openai")
gsk.llm.set_llm_model("gpt-4-turbo-preview")
giskard.scanner.logger.setLevel("DEBUG")

report = gsk.scan(model, dataset, raise_exceptions=True)
print(report)

# %% Set up different LLM clients and run additional scans
# Setting up different LLM clients and running scans with
