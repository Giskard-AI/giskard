# Newspaper classification with `torchtext`

## Libraries import
```python
import numpy as np
import pandas as pd
import torch
from torch import nn
from torchtext.data.functional import to_map_style_dataset
from torchtext.data.utils import get_tokenizer
from torchtext.datasets import AG_NEWS
from torchtext.vocab import build_vocab_from_iterator

import tests.utils
from giskard import Model, Dataset
```
## Wrap dataset
```python
train_iter = AG_NEWS(split="train")
test_iter = AG_NEWS(split="test")
ag_news_label = {1: "World", 2: "Sports", 3: "Business", 4: "Sci/Tec"}

test_dataset = to_map_style_dataset(test_iter)
raw_data = {
    "text": [value[1] for value in test_dataset],
    "label": [ag_news_label[value[0]] for value in test_dataset],
}
df = pd.DataFrame(raw_data, columns=["text", "label"])
```
```python
wrapped_dataset = Dataset(df.head(), 
                               name="test dataset", 
                               target="label")
```

## Wrap model
```python
num_class = len(ag_news_label.keys())

tokenizer = get_tokenizer("basic_english")


def yield_tokens(data_iter):
    for _, text in data_iter:
        yield tokenizer(text)


vocab = build_vocab_from_iterator(yield_tokens(train_iter), specials=["<unk>"])
vocab.set_default_index(vocab["<unk>"])


def text_pipeline(x):
    return vocab(tokenizer(x))


def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=0)


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


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

vocab_size = len(vocab)
emsize = 64
model = TextClassificationModel(vocab_size, emsize, num_class).to(device)

feature_names = ["text"]

class MyPyTorchModel(Model):

    def model_predict(self, df):
        def predict_proba(text):
            with torch.no_grad():
                text = torch.tensor(text_pipeline(text))
                output = self.model(text, torch.tensor([0]))
                np_output = output.numpy()[0]
                return softmax(np_output)

        def prediction_function(df):
            series = df["text"].apply(predict_proba)
            return np.array(series.tolist())

        return prediction_function(df)
```
```python
wrapped_model = MyPyTorchModel(model=model,
                                feature_names=feature_names,
                                model_type="classification",
                                classification_labels=list(ag_news_label.values()))
```
