from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM

from giskard import Model, Dataset
import pandas as pd
from giskard.scanner import Scanner


def test_generative_model_dataset():
    llm = FakeListLLM(responses=["He was a great cooker", "[He/She] was a bad Data Scientist"] * 100)
    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(
        pd.DataFrame({"instruct": ["Paraphrase this", "Answer this question"]}),
        column_types={
            "instruct": "text",
        },
    )

    scanner = Scanner(only=["gender"])
    result = scanner.analyze(model, dataset)
    assert result.has_issues()
