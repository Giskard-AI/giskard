from giskard.client.project import GiskardProject
import pytest
import torchtext
from torchtext.functional import to_tensor

@pytest.mark.skip(reason="Will be solved in the new API: https://github.com/Giskard-AI/giskard/pull/618")
def test_XLMR_BASE_ENCODER():

    xlmr_base = torchtext.models.XLMR_BASE_ENCODER
    model = xlmr_base.get_model()
    transform = xlmr_base.transform()
    #input_batch = ["Hello world", "How are you!"]
    #df = pd.DataFrame(input_batch,columns=['text'])
    def prediction_function(df):
        input_batch = df['text'].values.tolist()
        model_input = to_tensor(transform(input_batch), padding_value=1)
        output = model(model_input)

        return output.cpu().detach().numpy()

    GiskardProject._validate_model_is_pickleable(prediction_function)