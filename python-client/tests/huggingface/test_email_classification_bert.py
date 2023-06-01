import email
from collections import defaultdict

import pandas as pd
from dateutil import parser
from scipy import special
from transformers import BertTokenizer, BertForSequenceClassification

import email_classification_utils
import tests.utils
from giskard import HuggingFaceModel, Dataset

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


def test_email_classification_bert_custom_model():
    email_files = email_classification_utils.get_email_files()

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

    def preprocessing_func(test_dataset):
        test_dataset = test_dataset.squeeze(axis=1)
        X_test = list(test_dataset)
        X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512, return_tensors="pt")
        return X_test_tokenized

    my_model = HuggingFaceModel(
        name=model_name,
        clf=model,
        feature_names=['Content'],
        model_type="classification",
        classification_labels=list(classification_labels_mapping.keys()),
        data_preprocessing_function=preprocessing_func,
    )

    my_test_dataset = Dataset(data_filtered.head(5), name="test dataset", target="Target",
                              cat_columns=['Week_day', 'Month'])

    tests.utils.verify_model_upload(my_model, my_test_dataset)
