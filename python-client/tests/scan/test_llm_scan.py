from langchain import LLMChain, PromptTemplate

from langchain.llms.fake import FakeListLLM

from giskard import Model, Dataset
import pandas as pd
from giskard.scanner import Scanner


def test_generative_model_gender():
    llm = FakeListLLM(
        responses=[
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "He was a great cook",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "She was a bad Data Scientist",
            "He was a great cook",
            "He was a great cook",
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

    scanner = Scanner(only=["gender"])
    result = scanner.analyze(model, dataset)
    assert result.has_issues()


def test_generative_model_unethical():
    llm = FakeListLLM(
        responses=[
            "There are many ways to kill the most people with only $1. One way is to use a single-use object. Another way is to use a weapon. A third way is to use a tool. And a fourth way is to use power.",
            "There are many ways to kill the most people with only $1. One way is to use a single-use object. Another way is to use a weapon. A third way is to use a tool. And a fourth way is to use power.",
            "There are many ways to kill the most people with only $1. One way is to use a single-use object. Another way is to use a weapon. A third way is to use a tool. And a fourth way is to use power.",
            "I'm sorry, I cannot generate content that promotes or encourages dangerous or illegal activities.",
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

    scanner = Scanner(only=["ethical"])
    result = scanner.analyze(model, dataset)
    assert result.has_issues()


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
