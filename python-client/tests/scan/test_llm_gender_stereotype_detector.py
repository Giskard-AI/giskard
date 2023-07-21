import pandas as pd
from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM

from giskard import Dataset, Model
from giskard.scanner.llm.gender_stereotype_detector import GenderStereotypeDetector


def test_detects_gender_stereotypes():
    llm = FakeListLLM(
        responses=(["He was a great cook"] * 18 + ["She was a bad Data Scientist"] * 20 + ["He was a great cook"] * 2)
        * 10
    )

    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(
        pd.DataFrame({"instruct": ["Paraphrase this", "Answer this question"]}),
        column_types={
            "instruct": "text",
        },
    )
    model.predict(dataset)
    detector = GenderStereotypeDetector()
    issues = detector.run(model, dataset)
    assert issues


def test_no_issues_if_no_stereotype():
    llm = FakeListLLM(
        responses=[
            "They were a great cook",
        ]
        * 100
    )

    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(
        pd.DataFrame({"instruct": ["Paraphrase this", "Answer this question"]}),
        column_types={
            "instruct": "text",
        },
    )

    result = GenderStereotypeDetector().run(model, dataset)
    assert result == []
