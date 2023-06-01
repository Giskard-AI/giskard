import giskard
import numpy as np
import pandas as pd
from giskard.scanner.robustness.text_perturbation_detector import TextPerturbationDetector


def test_perturbation_classification(enron_model, enron_data):
    analyzer = TextPerturbationDetector(threshold=0.01)
    res = analyzer.run(enron_model, enron_data)
    assert res


def test_text_perturbation_skips_non_textual_dtypes():
    # We make an int feature…
    df = pd.DataFrame({"feature": [1, 2, 3, 4, 5], "target": [0, 0, 1, 1, 0]})
    # …but we declare it as text
    ds = giskard.Dataset(df, target="target", column_types={"feature": "text"})

    model = giskard.Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1])
    analyzer = TextPerturbationDetector(threshold=0.01)
    issues = analyzer.run(model, ds)

    assert not issues


def test_text_perturbation_works_with_nan_values():
    df = pd.DataFrame({"feature": ["Satius est supervacua scire", "quam nihil", np.nan], "target": [1, 0, 1]})
    ds = giskard.Dataset(df, target="target", column_types={"feature": "text"})

    analyzer = TextPerturbationDetector(threshold=0.01)
    model = giskard.Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1])

    issues = analyzer.run(model, ds)

    assert len(issues) == 0


def test_llm_text_transformation():
    from langchain import LLMChain, PromptTemplate
    from langchain.chat_models import ChatOpenAI
    from giskard import Model, Dataset

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = PromptTemplate(template="{instruct}: {question}", input_variables=["instruct", "question"])
    chain = LLMChain(prompt=prompt, llm=llm)

    model = Model(chain, model_type='generative')

    dataset = Dataset(pd.DataFrame({
        "instruct": ["Paraphrase this", "Answer this question"],
        "question": ["Who is the mayor of Rome?", "How many bridges are there in Paris?"]
    }), column_types={"instruct": "text", "question": "text"})

    prediction = model.predict(dataset)
    assert prediction

    analyzer = TextPerturbationDetector()
    analyzer.run(model, dataset)
