import pandas as pd
import tests.utils
import numpy as np
import pandas as pd
import torch
from torch import nn
from torchtext.data.functional import to_map_style_dataset
from torchtext.data.utils import get_tokenizer
from torchtext.datasets import AG_NEWS
from torchtext.vocab import build_vocab_from_iterator
import email
from collections import defaultdict

from dateutil import parser
from scipy import special
from transformers import BertTokenizer, BertForSequenceClassification

from tests.huggingface.email_classification_utils import get_email_files
import tests.utils

import tests.utils
from giskard import Dataset

from giskard.models.automodel import Model

train_iter = AG_NEWS(split="train")
test_iter = AG_NEWS(split="test")
ag_news_label = {1: "World", 2: "Sports", 3: "Business", 4: "Sci/Tec"}
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


idx_to_cat = {
    1: 'REGULATION',
    2: 'INTERNAL',
    3: 'INFLUENCE',
    4: 'INFLUENCE',
    5: 'INFLUENCE',
    6: 'CALIFORNIA CRISIS',
    7: 'INTERNAL',
    8: 'INTERNAL',
    9: 'INFLUENCE',
    10: 'REGULATION',
    11: 'talking points',
    12: 'meeting minutes',
    13: 'trip reports'}

LABEL_CAT = 3


def my_softmax(x):
    return special.softmax(x, axis=1)


# get_labels returns a dictionary representation of these labels.
def get_labels(filename):
    with open(filename + '.cats') as f:
        labels = defaultdict(dict)
        line = f.readline()
        while line:
            line = line.split(',')
            top_cat, sub_cat, freq = int(line[0]), int(line[1]), int(line[2])
            labels[top_cat][sub_cat] = freq
            line = f.readline()
    return dict(labels)


def test_autoserializablemodel_sklearn(german_credit_raw_model, german_credit_data):
    class my_custom_model(Model):
        def model_predict(self, some_df: pd.DataFrame):
            return self.model.predict_proba(some_df)

    my_model = my_custom_model(
        model=german_credit_raw_model,
        model_type="classification",
        classification_labels=german_credit_raw_model.classes_,
        classification_threshold=0.5,
    )

    tests.utils.verify_model_upload(my_model, german_credit_data)


def test_autoserializablemodel_pytorch():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    vocab_size = len(vocab)
    emsize = 64
    model = TextClassificationModel(vocab_size, emsize, num_class).to(device)

    test_dataset = to_map_style_dataset(test_iter)
    raw_data = {
        "text": [value[1] for value in test_dataset],
        "label": [ag_news_label[value[0]] for value in test_dataset],
    }
    df = pd.DataFrame(raw_data, columns=["text", "label"])

    feature_names = ["text"]

    class my_PyTorchModel(Model):

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

    my_model = my_PyTorchModel(
        name="my_custom_BertForSequenceClassification",
        model=model,
        feature_names=feature_names,
        model_type="classification",
        classification_labels=list(ag_news_label.values()),
    )

    # defining the giskard dataset
    my_test_dataset = Dataset(df.head(), name="test dataset", target="label")

    my_model.predict(my_test_dataset)

    tests.utils.verify_model_upload(my_model, my_test_dataset)


def test_autoserializablemodel_huggingface():
    email_files = get_email_files()

    columns_name = ['Target', 'Subject', 'Content', 'Week_day', 'Year', 'Month', 'Hour', 'Nb_of_forwarded_msg']

    data_list = []
    for email_file in email_files:
        values_to_add = {}

        # Target is the sub-category with maximum frequency
        if LABEL_CAT in get_labels(email_file):
            sub_cat_dict = get_labels(email_file)[LABEL_CAT]
            target_int = max(sub_cat_dict, key=sub_cat_dict.get)
            values_to_add['Target'] = str(idx_to_cat[target_int])

        # Features are metadata from the email object
        filename = email_file + '.txt'
        with open(filename) as f:

            message = email.message_from_string(f.read())

            values_to_add['Subject'] = str(message['Subject'])
            values_to_add['Content'] = str(message.get_payload())

            date_time_obj = parser.parse(message['Date'])
            values_to_add['Week_day'] = date_time_obj.strftime("%A")
            values_to_add['Year'] = date_time_obj.strftime("%Y")
            values_to_add['Month'] = date_time_obj.strftime("%B")
            values_to_add['Hour'] = int(date_time_obj.strftime("%H"))

            # Count number of forwarded mails
            number_of_messages = 0
            for line in message.get_payload().split('\n'):
                if ('forwarded' in line.lower() or 'original' in line.lower()) and '--' in line:
                    number_of_messages += 1
            values_to_add['Nb_of_forwarded_msg'] = number_of_messages

        data_list.append(values_to_add)

    data = pd.DataFrame(data_list, columns=columns_name)

    # We filter 879 rows (if Primary topics exists (i.e. if coarse genre 1.1 is selected) )
    data_filtered = data[data["Target"].notnull()]

    # Exclude target category with very few rows ; 812 rows remains
    excluded_category = [idx_to_cat[i] for i in [11, 12, 13]]
    data_filtered = data_filtered[-data_filtered["Target"].isin(excluded_category)]

    # Define pretrained tokenizer and model
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2"

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    for param in model.base_model.parameters():
        param.requires_grad = False

    classification_labels_mapping = {'REGULATION': 0, 'INTERNAL': 1, 'CALIFORNIA CRISIS': 2, 'INFLUENCE': 3}

    # Based on the documentation: https://huggingface.co/cross-encoder/ms-marco-TinyBERT-L-2
    # ---------------------------------------------------------------------------------------
    def preprocessing_func(test_dataset):
        test_dataset = test_dataset.squeeze(axis=1)
        X_test = list(test_dataset)
        X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512, return_tensors="pt")
        return X_test_tokenized

    class tiny_bert_HuggingFaceModel(Model):
        def model_predict(self, data):
            with torch.no_grad():
                predictions = self.model(**data).logits
            return predictions.detach().cpu().numpy()

    # ---------------------------------------------------------------------------------------

    my_model = tiny_bert_HuggingFaceModel(name=model_name,
                                          model=model,
                                          feature_names=['Content'],
                                          model_type="classification",
                                          classification_labels=list(classification_labels_mapping.keys()),
                                          data_preprocessing_function=preprocessing_func,
                                          model_postprocessing_function=my_softmax)

    my_test_dataset = Dataset(data_filtered.head(5), name="test dataset", target="Target",
                              cat_columns=['Week_day', 'Month'])

    tests.utils.verify_model_upload(my_model, my_test_dataset)
