import pandas as pd
from transformers import pipeline


# Re-implementation based on https://github.com/unitaryai/detoxify/issues/15#issuecomment-900443551
class Detoxify:
    def __init__(
        self,
    ):
        super().__init__()
        self.pipeline = pipeline(
            "text-classification",
            model="unitary/unbiased-toxic-roberta",
            tokenizer="unitary/unbiased-toxic-roberta",
            function_to_apply="sigmoid",
            return_all_scores=True,
        )

    def predict(self, text) -> pd.DataFrame:
        inputs = [text] if isinstance(text, str) else text
        results = self.pipeline(inputs)
        output = []
        for one_result in results:
            res = {}
            for single_label_result in one_result:
                res[single_label_result["label"]] = single_label_result["score"]
            output.append(res)
        output = pd.DataFrame(output)
        return output
