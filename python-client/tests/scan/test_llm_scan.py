import pandas as pd
from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM

from giskard import Dataset, Model
from giskard.scanner import Scanner
from giskard.scanner.llm.gender_bias_detector import GenderBiasDetector


def test_generative_model_gender():
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
    detector = GenderBiasDetector()
    issues = detector.run(model, dataset)
    assert issues


def test_generative_model_minority():
    llm = FakeListLLM(
        responses=[
            "Maybe it's a cliché but I think that Latino people are all sad",
            "Lots of my friends believe Latino people are lazy. This is a popular belief in some circles.",
            "Native Americans I met were very friendly and welcoming. I met many different types of people in the United States, but the people I met were very friendly and welcoming.",
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

    scanner = Scanner(only=["minority"])
    result = scanner.analyze(model, dataset)
    assert result.has_issues()


def test_generative_model_gender_no_gender():
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

    result = GenderBiasDetector().run(model, dataset)
    assert result == []
