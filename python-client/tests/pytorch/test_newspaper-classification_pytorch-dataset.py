import os
import re

import httpretty
import pandas as pd
import torch
from scipy import special
from torch import nn
from torch.utils.data import Dataset as torch_dataset
from torchtext.data.functional import to_map_style_dataset
from torchtext.data.utils import get_tokenizer
from torchtext.datasets import AG_NEWS
from torchtext.vocab import build_vocab_from_iterator

from giskard import PyTorchModel, Dataset
from giskard.client.giskard_client import GiskardClient

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"

train_iter = AG_NEWS(split='train')
test_iter = AG_NEWS(split='test')
ag_news_label = {1: "World",
                 2: "Sports",
                 3: "Business",
                 4: "Sci/Tec"}
num_class = len(ag_news_label.keys())

tokenizer = get_tokenizer('basic_english')


def yield_tokens(data_iter):
    for _, text in data_iter:
        yield tokenizer(text)


vocab = build_vocab_from_iterator(yield_tokens(train_iter), specials=["<unk>"])
vocab.set_default_index(vocab["<unk>"])

text_pipeline = lambda x: vocab(tokenizer(x))


class PandasToTorch(torch_dataset):
    def __init__(self, df: pd.DataFrame):
        # copy original df
        self.entries = df.copy()
        # transformation step
        self.entries['text'] = df['text'].apply(text_pipeline)

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        return torch.tensor(self.entries['text'].iloc[idx]), torch.tensor([0])


def my_softmax(x):
    return special.softmax(x, axis=1)


class TextClassificationModel(nn.Module):

    def __init__(self, vocab_size, embed_dim, num_class):
        super(TextClassificationModel, self).__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim, sparse=True)
        self.fc = nn.Linear(embed_dim, num_class)
        self.init_weights()

    def init_weights(self):
        initrange = 0.5
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()

    def forward(self, text, offsets):
        embedded = self.embedding(text, offsets)
        return self.fc(embedded)


# @pytest.mark.skip(reason="WIP")
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_newspaper_classification_pytorch_dataset():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    vocab_size = len(vocab)
    emsize = 64
    model = TextClassificationModel(vocab_size, emsize, num_class).to(device)

    test_dataset = to_map_style_dataset(test_iter)
    raw_data = {"text": [value[1] for value in test_dataset],
                "label": [ag_news_label[value[0]] for value in test_dataset]}
    df = pd.DataFrame(raw_data, columns=["text", "label"])

    feature_names = ['text']

    my_model = PyTorchModel(name="my_BertForSequenceClassification",
                            clf=model,
                            feature_names=feature_names,
                            model_type="classification",
                            classification_labels=list(ag_news_label.values()),
                            data_preprocessing_function=PandasToTorch,
                            model_postprocessing_function=my_softmax)

    # defining the giskard dataset
    my_test_dataset = Dataset(df.head(), name="test dataset", target="label")

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")

    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, models_url_pattern)

    client = GiskardClient(url, token)
    # enron = client.create_project('test-project', "Email Classification", "Email Classification")
    my_model.upload(client, 'test-project', my_test_dataset)

    assert re.match("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", str(my_model.id))

    artifact_requests = [i for i in httpretty.latest_requests() if artifact_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0

    artifact_requests = [i for i in httpretty.latest_requests() if models_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0
        assert req.headers.get("Content-Type") == "application/json"

    os.system("rm -r output enron_with_categories")
