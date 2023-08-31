import pandas as pd
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM
from langchain.prompts import PromptTemplate

import tests.utils
from giskard import Dataset, Model


def test_llm_chain():
    responses = [
        "\n\nHueFoots.",
        "\n\nEcoDrive Motors.",
        "\n\nRainbow Socks.",
        "\n\nNoOil Motors.",
    ]
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
