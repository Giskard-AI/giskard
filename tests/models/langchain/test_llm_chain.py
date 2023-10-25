import tempfile

import pandas as pd
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM
from langchain.prompts import PromptTemplate

import tests.utils
from giskard import Dataset, Model
from giskard.models.langchain import LangchainModel


def test_llm_chain():
    responses = ["\n\nHueFoots.", "\n\nEcoDrive Motors."]
    llm = FakeListLLM(responses=responses)
    prompt = PromptTemplate(
        input_variables=["product"],
        template="What is a good name for a company that makes {product}?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    wrapped_model = Model(chain, model_type="text_generation")

    df = pd.DataFrame(["colorful socks", "electric car"], columns=["product"])

    wrapped_dataset = Dataset(df, cat_columns=[])

    tests.utils.verify_model_upload(wrapped_model, wrapped_dataset)

    results = wrapped_model.predict(wrapped_dataset)

    assert list(results.raw) == responses[:2], f"{results.raw}"
    assert list(results.raw_prediction) == responses[:2]

    with tempfile.TemporaryDirectory() as tmpdirname:
        wrapped_model.save(tmpdirname)
        loaded_model = LangchainModel.load(tmpdirname)

        assert list(results.raw) == list(loaded_model.predict(wrapped_dataset).raw)
