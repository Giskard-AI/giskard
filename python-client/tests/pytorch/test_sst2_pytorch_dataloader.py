import re

import httpretty
import pandas as pd
import requests_mock
import torch
import torchtext.functional as F
import torchtext.transforms as T
from scipy import special
from torch.hub import load_state_dict_from_url
from torch.utils.data import DataLoader
from torchdata.datapipes.iter import IterableWrapper
from torchtext.datasets import SST2
from torchtext.models import RobertaClassificationHead, XLMR_BASE_ENCODER

import tests.utils
from giskard import PyTorchModel, Dataset
from giskard.client.giskard_client import GiskardClient


def my_softmax(x):
    return special.softmax(x, axis=1)


device = 'cuda' if torch.cuda.is_available() else 'cpu'

padding_idx = 1
bos_idx = 0
eos_idx = 2
max_seq_len = 256
xlmr_vocab_path = r"https://download.pytorch.org/models/text/xlmr.vocab.pt"
xlmr_spm_model_path = r"https://download.pytorch.org/models/text/xlmr.sentencepiece.bpe.model"

text_transform = T.Sequential(
    T.SentencePieceTokenizer(xlmr_spm_model_path),
    T.VocabTransform(load_state_dict_from_url(xlmr_vocab_path)),
    T.Truncate(max_seq_len - 2),
    T.AddToken(token=bos_idx, begin=True),
    T.AddToken(token=eos_idx, begin=False),
)
batch_size = 16

dev_datapipe = SST2(split="dev")
dev_dataframe = pd.DataFrame(dev_datapipe, columns=["text", "label"])

num_classes = 2
input_dim = 768

classifier_head = RobertaClassificationHead(num_classes=num_classes, input_dim=input_dim)
model = XLMR_BASE_ENCODER.get_model(head=classifier_head, load_weights=False).to(device)


# Transform the raw dataset using non-batched API (i.e apply transformation line by line)
def apply_transform(x):
    return text_transform(x[0]), x[1]


def test_sst2_pytorch_dataloader():
    def collate_batch(batch):
        return F.to_tensor(batch["token_ids"], padding_value=padding_idx).to(device)

    def pandas_to_torch(test_df):
        test_datapipe_transformed = IterableWrapper(test_df['text']).map(apply_transform)
        test_datapipe_transformed = test_datapipe_transformed.batch(batch_size)
        test_datapipe_transformed = test_datapipe_transformed.rows2columnar(["token_ids", "target"])
        return DataLoader(test_datapipe_transformed, batch_size=None, collate_fn=collate_batch)

    classification_labels = ['0', '1']
    my_model = PyTorchModel(name='SST2-XLMR_BASE_ENCODER',
                            clf=model,
                            feature_names=['text'],
                            model_type="classification",
                            classification_labels=classification_labels,
                            data_preprocessing_function=pandas_to_torch,
                            model_postprocessing_function=my_softmax)

    # defining the giskard dataset
    my_test_dataset = Dataset(dev_dataframe.head(), name="test dataset", target="label")

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")

    with requests_mock.Mocker() as m:
        m.register_uri(httpretty.POST, artifact_url_pattern)
        m.register_uri(httpretty.POST, models_url_pattern)
        m.register_uri(httpretty.GET, settings_url_pattern)

        url = "http://giskard-host:12345"
        token = "SECRET_TOKEN"
        client = GiskardClient(url, token)
        my_model.upload(client, 'test-project', my_test_dataset)

        tests.utils.match_model_id(my_model.id)
        tests.utils.match_url_patterns(m.request_history, artifact_url_pattern)
        tests.utils.match_url_patterns(m.request_history, models_url_pattern)
