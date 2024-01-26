import tempfile
from pathlib import Path

import pandas as pd
from langchain.chains import LLMChain, load_chain
from langchain.chains.base import Chain
from langchain.llms.fake import FakeListLLM

import giskard

TEXT_COLUMN_NAME = "query"


class MyModel(giskard.Model):
    def model_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[TEXT_COLUMN_NAME].apply(lambda x: self.model.run({"query": x}))

    def save_model(self, path: str, *args, **kwargs):
        out_dest = Path(path)
        # Save the chain object
        self.model.save(out_dest.joinpath("model.json"))

    @classmethod
    def load_model(cls, path: str, **kwargs) -> Chain:
        src = Path(path)

        # Load the chain, passing the retriever
        chain = load_chain(src.joinpath("model.json"))
        return chain


def test_load():
    llm = FakeListLLM(responses=["foo", "bar", "baz"])
    chain = LLMChain.from_string(llm=llm, template="{query}")

    model = MyModel(
        chain,
        "text_generation",
        name="Foo",
        description="Model that reply foo, bar, baz",
        feature_names=[TEXT_COLUMN_NAME],
    )

    with tempfile.TemporaryDirectory() as f:
        model.save(f)
        giskard.Model.load(f)
