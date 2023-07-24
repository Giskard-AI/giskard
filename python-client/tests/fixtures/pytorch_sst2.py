import pandas as pd
import pytest
import torch
import torch.nn as nn
import torchtext.functional as F
import torchtext.transforms as T
from torch.hub import load_state_dict_from_url
from torchtext.datasets import SST2
from torchtext.models import XLMR_BASE_ENCODER, RobertaClassificationHead

from giskard import Dataset
from giskard.models.pytorch import PyTorchModel
from tests.utils import resource_dir


@pytest.fixture()
def sst2_dev_data():
    dev_datapipe = SST2(split="dev")
    return pd.DataFrame(dev_datapipe, columns=["text", "label"])


@pytest.fixture()
def sst2_data(sst2_dev_data):
    return Dataset(sst2_dev_data.head(), name="test dataset", target="label")


@pytest.fixture()
def sst2_model(sst2_dev_data):
    torch_softmax = nn.Softmax(dim=1)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    padding_idx = 1
    bos_idx = 0
    eos_idx = 2
    max_seq_len = 256
    xlmr_vocab_path = r"https://download.pytorch.org/models/text/xlmr.vocab.pt"
    xlmr_spm_model_path = r"https://download.pytorch.org/models/text/xlmr.sentencepiece.bpe.model"

    text_transform = T.Sequential(
        T.SentencePieceTokenizer(xlmr_spm_model_path),
        T.VocabTransform(load_state_dict_from_url(xlmr_vocab_path, model_dir=resource_dir)),
        T.Truncate(max_seq_len - 2),
        T.AddToken(token=bos_idx, begin=True),
        T.AddToken(token=eos_idx, begin=False),
    )

    num_classes = 2
    input_dim = 768

    classifier_head = RobertaClassificationHead(num_classes=num_classes, input_dim=input_dim)
    model = XLMR_BASE_ENCODER.get_model(head=classifier_head, load_weights=False).to(device)

    def pandas_to_torch(test_df):
        return [F.to_tensor(text_transform(test_df.text.tolist()), padding_value=padding_idx)]

    classification_labels = [0, 1]

    def my_softmax(x):
        return torch_softmax(x)

    return PyTorchModel(
        name="SST2-XLMR_BASE_ENCODER",
        model=model,
        feature_names=["text"],
        model_type="classification",
        classification_labels=classification_labels,
        data_preprocessing_function=pandas_to_torch,
        model_postprocessing_function=my_softmax,
    )
