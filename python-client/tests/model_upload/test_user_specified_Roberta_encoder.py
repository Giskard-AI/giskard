from torchtext.models import RobertaEncoderConf, RobertaBundle, RobertaClassificationHead
from giskard.client.project import GiskardProject
import torch, torchtext
from torchtext.functional import to_tensor
import pandas as pd

def test_user_specified_Roberta_encoder():
    model_weights_path = "https://download.pytorch.org/models/text/xlmr.base.encoder.pt"
    encoder_conf = RobertaEncoderConf(vocab_size=250002)
    classifier_head = RobertaClassificationHead(num_classes=2, input_dim=768)
    model = RobertaBundle.build_model(encoder_conf=encoder_conf, head=classifier_head, checkpoint=model_weights_path)

    temp_xlmr_base = torchtext.models.XLMR_BASE_ENCODER
    transform = temp_xlmr_base.transform()

    def prediction_function(df):
        input_batch = df['text'].values.tolist()
        model_input = to_tensor(transform(input_batch), padding_value=1)
        output = model(model_input)
        return output.cpu().detach().numpy()

    GiskardProject._validate_model_is_pickleable(prediction_function)