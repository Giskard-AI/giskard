import email
import glob
import os
from collections import defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from string import punctuation

import pandas as pd
from dateutil import parser
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer


from sklearn.linear_model import LogisticRegression
from sklearn import model_selection

def test_EmailClassification():

    os.system("wget http://bailando.sims.berkeley.edu/enron/enron_with_categories.tar.gz")
    os.system("tar zxf enron_with_categories.tar.gz")
    os.system("rm enron_with_categories.tar.gz")


    nltk.download('punkt')
    nltk.download('stopwords')

    stoplist = set(stopwords.words('english') + list(punctuation))
    stemmer = PorterStemmer()

    # http://bailando.sims.berkeley.edu/enron/enron_categories.txt
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

    idx_to_cat2 = {
        1: 'regulations and regulators (includes price caps)',
        2: 'internal projects -- progress and strategy',
        3: ' company image -- current',
        4: 'company image -- changing / influencing',
        5: 'political influence / contributions / contacts',
        6: 'california energy crisis / california politics',
        7: 'internal company policy',
        8: 'internal company operations',
        9: 'alliances / partnerships',
        10: 'legal advice',
        11: 'talking points',
        12: 'meeting minutes',
        13: 'trip reports'}


    LABEL_CAT = 3  # we'll be using the 2nd-level category "Primary topics" because the two first levels provide categories that are not mutually exclusive. see : https://bailando.berkeley.edu/enron/enron_categories.txt

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


    email_files = [f.replace('.cats', '') for f in glob.glob('enron_with_categories/*/*.cats')]

    columns_name = ['Target', 'Subject', 'Content', 'Week_day', 'Year', 'Month', 'Hour', 'Nb_of_forwarded_msg']
    data = pd.DataFrame(columns=columns_name)

    for email_file in email_files:
        values_to_add = {}

        # Target is the sub-category with maximum frequency
        if LABEL_CAT in get_labels(email_file):
            sub_cat_dict = get_labels(email_file)[LABEL_CAT]
            target_int = max(sub_cat_dict, key=sub_cat_dict.get)
            values_to_add['Target'] = str(idx_to_cat[target_int])

        # Features are metadata from the email object
        filename = email_file+'.txt'
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

        row_to_add = pd.Series(values_to_add)
        data = data.append(row_to_add, ignore_index=True)

    # We filter 879 rows (if Primary topics exists (i.e. if coarse genre 1.1 is selected) )
    data_filtered = data[data["Target"].notnull()]

    #Exclude target category with very few rows ; 812 rows remains
    excluded_category = [idx_to_cat[i] for i in [11,12,13]]
    data_filtered = data_filtered[data_filtered["Target"].isin(excluded_category) == False]
    num_classes = len(data_filtered["Target"].value_counts())

    column_types={
        'Target': "category",
        "Subject": "text",
        "Content": "text",
        "Week_day": "category",
        "Month": "category",
        "Hour": "numeric",
        "Nb_of_forwarded_msg": "numeric",
        "Year": "numeric"
    }

    feature_types = {i:column_types[i] for i in column_types if i!='Target'}

    columns_to_scale = [key for key in feature_types.keys() if feature_types[key]=="numeric"]

    numeric_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')),
                                    ('scaler', StandardScaler())])


    columns_to_encode = [key for key in feature_types.keys() if feature_types[key]=="category"]

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore',sparse=False)) ])
    text_transformer = Pipeline([
        ('vect', CountVectorizer(stop_words=stoplist)),
        ('tfidf', TfidfTransformer())
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, columns_to_scale),
            ('cat', categorical_transformer, columns_to_encode),
            ('text_Mail', text_transformer, "Content")
        ]
    )
    clf = Pipeline(steps=[('preprocessor', preprocessor)])

    feature_types = {i:column_types[i] for i in column_types if i!="Target"}
    Y = data_filtered["Target"]
    X = data_filtered.drop(columns=["Target"])
    X_train,X_test,Y_train,Y_test = model_selection.train_test_split(X, Y,test_size=0.20, random_state = 30, stratify = Y)

    clf.fit(X_train, Y_train)

    train_data = pd.concat([X_train, Y_train], axis=1)
    test_data = pd.concat([X_test, Y_test ], axis=1)


    #----- pytorch model
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score
    import torch
    from transformers import TrainingArguments, Trainer
    from transformers import BertTokenizer, BertForSequenceClassification

    np.random.seed(112)

    # Read data
    data = data_filtered

    # Define pretrained tokenizer and model
    # model_name = "bert-base-uncased" # For large BERT Model
    model_name = "cross-encoder/ms-marco-TinyBERT-L-2" # For tiny BERT Model

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    for param in model.base_model.parameters():
        param.requires_grad = False

    # ----- 1. Preprocess data -----#
    # Preprocess data

    X = list(data["Content"])
    classification_labels_mapping = {'REGULATION': 0,'INTERNAL': 1,'CALIFORNIA CRISIS': 2,'INFLUENCE': 3}
    y = list(data_filtered['Target'].map(classification_labels_mapping))

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
    X_train_tokenized = tokenizer(X_train, padding=True, truncation=True, max_length=128)
    X_val_tokenized = tokenizer(X_val, padding=True, truncation=True, max_length=128)

    # Create torch dataset
    class Dataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels=None):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            if self.labels:
                item["labels"] = torch.tensor(self.labels[idx])
            return item

        def __len__(self):
            return len(self.encodings["input_ids"])

    train_dataset = Dataset(X_train_tokenized, y_train)
    val_dataset = Dataset(X_val_tokenized, y_val)

    # ----- 2. Fine-tune pretrained model -----#
    # Define Trainer parameters
    def compute_metrics(p):
        pred, labels = p
        pred = np.argmax(pred, axis=1)

        accuracy = accuracy_score(y_true=labels, y_pred=pred)
        recall = recall_score(y_true=labels, y_pred=pred, average='macro')
        precision = precision_score(y_true=labels, y_pred=pred, average='macro')
        f1 = f1_score(y_true=labels, y_pred=pred, average='macro')

        return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

    # Define Trainer
    args = TrainingArguments(
        output_dir="output",
        evaluation_strategy="steps",
        eval_steps=500,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=1,
        seed=0,
        load_best_model_at_end=True,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    # Train pre-trained model
    trainer.train()

    def predict(test_dataset):
        test_dataset= test_dataset.squeeze(axis=1)
        X_test = list(test_dataset)
        X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512)

        # Create torch dataset
        test_dataset = Dataset(X_test_tokenized)

        # Define test trainer
        test_trainer = Trainer(model)

        # Make prediction
        raw_pred, _, _ = test_trainer.predict(test_dataset)
        predictions = torch.nn.functional.softmax(torch.from_numpy(raw_pred), dim=-1)
        predictions = predictions.cpu().detach().numpy()

        return predictions

    feature_names = ['Content']
    test_df = data_filtered[feature_names][:5]

    test_dataset= test_df.squeeze(axis=1)
    X_test = list(test_dataset)
    X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512, return_tensors="pt")

    # Create torch dataset
    test_dataset = Dataset(X_test_tokenized)


    with torch.no_grad():
        logits = model(**X_test_tokenized).logits
        predictions = torch.nn.functional.softmax(logits, dim=-1)
        predictions = predictions.cpu().detach().numpy()

    print(predictions)

    print(predict(test_df))

    from giskard import Model, PyTorchModel, GiskardClient, Dataset

    # Wrap your clf with PyTorchModel from Giskard
    def preparation_function(test_df):
        test_dataset= test_df.squeeze(axis=1)
        X_test = list(test_dataset)
        X_test_tokenized = tokenizer(X_test, padding=True, truncation=True, max_length=512, return_tensors="pt")
        test_dataset = Dataset(X_test_tokenized)
        return test_dataset

    my_model = PyTorchModel(name="BertForSequenceClassification",
                            clf=model,
                            feature_names=feature_names,
                            model_type="classification",
                            classification_labels=list(classification_labels_mapping.keys()),
                            data_preprocessing_function=preparation_function)

    # Wrap your dataset with Dataset from Giskard
    my_test_dataset = Dataset(data_filtered[['Content','Target']].head(), name="test dataset", target="Target")

    from giskard.core.model_validation import validate_model

    validate_model(my_model, validate_ds=my_test_dataset)


if __name__=="__main__":
    test_EmailClassification()