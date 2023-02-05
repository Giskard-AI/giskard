import pandas as pd
import numpy as np
from scipy import special
import pytest
import time
import torch
from torchtext.datasets import AG_NEWS
train_iter = iter(AG_NEWS(split='train'))

from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator
from torch.utils.data.dataset import random_split
from torchtext.data.functional import to_map_style_dataset
from torch.utils.data import DataLoader
from torch.utils.data import Dataset as torch_dataset

from torch import nn

from giskard.core.model_validation import validate_model
from giskard.client.giskard_client import GiskardClient
from giskard import PyTorchModel, Dataset

import re
import httpretty
url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"

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

#@pytest.mark.skip(reason="WIP")
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_text_sentiment_ngrams_tutorial():

    train_iter = AG_NEWS(split='train')
    num_class = len(set([label for (label, text) in train_iter]))

    tokenizer = get_tokenizer('basic_english')

    def yield_tokens(data_iter):
        for _, text in data_iter:
            yield tokenizer(text)

    train_iter = AG_NEWS(split='train')

    vocab = build_vocab_from_iterator(yield_tokens(train_iter), specials=["<unk>"])
    vocab.set_default_index(vocab["<unk>"])

    text_pipeline = lambda x: vocab(tokenizer(x))
    label_pipeline = lambda x: int(x) - 1

    def collate_batch(batch):
        label_list, text_list, offsets = [], [], [0]
        for (_label, _text) in batch:
            label_list.append(label_pipeline(_label))
            processed_text = torch.tensor(text_pipeline(_text), dtype=torch.int64)
            text_list.append(processed_text)
            offsets.append(processed_text.size(0))
        label_list = torch.tensor(label_list, dtype=torch.int64)
        offsets = torch.tensor(offsets[:-1]).cumsum(dim=0)
        text_list = torch.cat(text_list)
        return label_list.to(device), text_list.to(device), offsets.to(device)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_iter = AG_NEWS(split='train')
    dataloader = DataLoader(train_iter, batch_size=8, shuffle=False, collate_fn=collate_batch)


    vocab_size = len(vocab)
    emsize = 64
    model = TextClassificationModel(vocab_size, emsize, num_class).to(device)

    def evaluate(dataloader):
        model.eval()
        total_acc, total_count = 0, 0

        with torch.no_grad():
            for idx, (label, text, offsets) in enumerate(dataloader):
                predicted_label = model(text, offsets)
                loss = criterion(predicted_label, label)
                total_acc += (predicted_label.argmax(1) == label).sum().item()
                total_count += label.size(0)
        return total_acc/total_count

    def train(dataloader):
        model.train()
        total_acc, total_count = 0, 0
        log_interval = 500
        start_time = time.time()

        for idx, (label, text, offsets) in enumerate(dataloader):
            optimizer.zero_grad()
            predicted_label = model(text, offsets)
            loss = criterion(predicted_label, label)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
            optimizer.step()
            total_acc += (predicted_label.argmax(1) == label).sum().item()
            total_count += label.size(0)
            if idx % log_interval == 0 and idx > 0:
                elapsed = time.time() - start_time
                print('| epoch {:3d} | {:5d}/{:5d} batches '
                      '| accuracy {:8.3f}'.format(epoch, idx, len(dataloader),
                                                  total_acc/total_count))
                total_acc, total_count = 0, 0
                start_time = time.time()

    # Hyperparameters
    EPOCHS = 1 # epoch
    LR = 5  # learning rate
    BATCH_SIZE = 64 # batch size for training

    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1.0, gamma=0.1)
    total_accu = None
    train_iter, test_iter = AG_NEWS()
    train_dataset = to_map_style_dataset(train_iter)
    test_dataset = to_map_style_dataset(test_iter)
    num_train = int(len(train_dataset) * 0.95)
    split_train_, split_valid_ = \
        random_split(train_dataset, [num_train, len(train_dataset) - num_train])

    train_dataloader = DataLoader(split_train_, batch_size=BATCH_SIZE,
                                  shuffle=True, collate_fn=collate_batch)
    valid_dataloader = DataLoader(split_valid_, batch_size=BATCH_SIZE,
                                  shuffle=True, collate_fn=collate_batch)
    test_dataloader = DataLoader(test_dataset, batch_size=BATCH_SIZE,
                                 shuffle=True, collate_fn=collate_batch)

    #--- training
    """for epoch in range(1, EPOCHS + 1):
        epoch_start_time = time.time()
        train(train_dataloader)
        accu_val = evaluate(valid_dataloader)
        if total_accu is not None and total_accu > accu_val:
            scheduler.step()
        else:
            total_accu = accu_val
        print('-' * 59)
        print('| end of epoch {:3d} | time: {:5.2f}s | '
              'valid accuracy {:8.3f} '.format(epoch,
                                               time.time() - epoch_start_time,
                                               accu_val))
        print('-' * 59)"""

    print('Checking the results of test dataset.')
    accu_test = evaluate(test_dataloader)
    print('test accuracy {:8.3f}'.format(accu_test))

    ag_news_label = {1: "World",
                     2: "Sports",
                     3: "Business",
                     4: "Sci/Tec"}

    test_dataset = to_map_style_dataset(test_iter)
    raw_data = { "text": [value[1] for value in test_dataset], "label": [ag_news_label[value[0]] for value in test_dataset]}
    df = pd.DataFrame(raw_data, columns=["text", "label"])


    #=== original implementation
    """def softmax(x):
        return np.exp(x) / np.sum(np.exp(x), axis=0)

    def predict_proba(text):
        with torch.no_grad():
            text = torch.tensor(text_pipeline(text))
            output = model(text, torch.tensor([0]))
            np_output = output.numpy()[0]
            return softmax(np_output)

    def prediction_function(df):
        series = df["text"].apply(predict_proba)
        return np.array(series.tolist())"""

    feature_names = ['text']

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
        return special.softmax(x,axis=1)

    my_model = PyTorchModel(name="my_BertForSequenceClassification",
                            clf=model,
                            feature_names=feature_names,
                            model_type="classification",
                            classification_labels= list(ag_news_label.values()),
                            data_preprocessing_function=PandasToTorch,
                            model_postprocessing_function=my_softmax)

    # defining the giskard dataset
    my_test_dataset = Dataset(df.head(), name="test dataset", target="label")

    print(my_model._raw_predict(PandasToTorch(df.head())))
    my_output = my_model.predict(my_test_dataset)
    print(my_output.raw)

    #validate_model(my_model, validate_ds=my_test_dataset)

    #TODO: ensure that httpretty works
    """httpretty.register_uri(httpretty.POST, "http://giskard-host:12345/api/v2/project/models/upload")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models/upload")
    httpretty.register_uri(httpretty.POST, models_url_pattern)

    client = GiskardClient(url, token)
    enron = client.create_project('test-project', "Email Classification", "Email Classification")
    model_id = my_model.save(client, 'test-project', my_test_dataset)"""

if __name__=="__main__":
    test_text_sentiment_ngrams_tutorial()
