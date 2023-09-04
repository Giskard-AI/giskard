import pandas as pd
from langchain import LLMChain, PromptTemplate
from langchain.llms import FakeListLLM

from giskard import Dataset, Model
from giskard.scanner.llm.harmfulness_detector import HarmfulnessDetector


def test_detects_harmful_content():
    llm = FakeListLLM(
        responses=[
            "There are many ways to kill the most people with only $1. One way is to use a single-use object. Another way is to use a weapon. A third way is to use a tool. And a fourth way is to use power.",
            "There are many ways to kill the most people with only $1. One way is to use a single-use object. Another way is to use a weapon. A third way is to use a tool. And a fourth way is to use power.",
        ]
        + ["I'm sorry, I cannot generate content that promotes or encourages dangerous or illegal activities."] * 100,
    )
    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(pd.DataFrame({"instruct": ["demo"]}))

    detector = HarmfulnessDetector(threshold=0.4)
    issues = detector.run(model, dataset)
    assert len(issues) == 1
    assert len(issues[0].examples(None)) == 2


def test_detects_no_issues_if_model_harmless():
    llm = FakeListLLM(
        responses=["I'm sorry, I cannot generate content that promotes or encourages dangerous or illegal activities."]
        * 100,
    )
    prompt = PromptTemplate(template="{instruct}", input_variables=["instruct"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(pd.DataFrame({"instruct": ["demo"]}))

    detector = HarmfulnessDetector()
    issues = detector.run(model, dataset)
    assert not issues
