from giskard.client.project import GiskardProject

from transformers import AutoTokenizer, TFAutoModel # This is old code
#from transformers import AutoTokenizer, TFBertModel # This is updated code

from os.path import join
import pandas as pd
import tensorflow as tf
import numpy as np
import logging
import pytest
logging.basicConfig(level=logging.INFO)

pd.set_option('display.max_colwidth', None)


def load_transformer_models(bert, special_tokens):
    """
    Objective: load the tokenizer we'll use and also the transfomer model

    Inputs:
        - bert, str: the name of models look at https://huggingface.co/models for all models
        - special_tokens, list: list of str, where they are tokens to be considered as one token
    Outputs:
        - tokenizer, transformers.tokenization_distilbert.DistilBertTokenizer: the tokenizer of the model
        - transformer_model, transformers.modeling_tf_distilbert.TFDistilBertModel: the transformer model that
                                                                                    we will use as base
                                                                                    (embedding model)
    """
    tokenizer = AutoTokenizer.from_pretrained(bert)

    tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})

    transformer_model = TFAutoModel.from_pretrained(bert) # This is old code
    #transformer_model = TFBertModel.from_pretrained(bert) # This is updated code

    return tokenizer, transformer_model



def get_model(max_length, transformer_model, num_labels, rate=0.5, name_model=False, PATH_MODELS=False):
    """
    Get a model from scratch or if we have weights load it to the model.

    Inputs:
        - max_length, int: the input shape of the data
        - transformer_model, transformers.modeling_tf_distilbert.TFDistilBertModel: the transformer model that
                                                                                    we will use as base
                                                                                    (embedding model - sentence here)
        - num_labels, int: the number of intents
        - name_model (optional), str: look for an already existing model should be the entire path
    Outputs:
        - model, tensorflow.python.keras.engine.functional.Functional: the final model we'll train
    """

    logging.info('Creating architecture...')

    input_ids_in = tf.keras.layers.Input(shape=(max_length,), name='input_token', dtype='int32')
    input_masks_in = tf.keras.layers.Input(shape=(max_length,), name='masked_token', dtype='int32')

    embedding_layer = transformer_model(input_ids_in, attention_mask=input_masks_in)[0][:,0,:] # This is old code
    #embedding_layer = transformer_model.bert(input_ids_in, attention_mask=input_masks_in)[0][:,0,:] # This is updated code
    output_layer = tf.keras.layers.Dropout(rate=rate, name='embedding_do_layer')(embedding_layer)
    transf_out = tf.keras.layers.Flatten()(output_layer)

    output = tf.keras.layers.Dense(num_labels, activation='sigmoid')(transf_out)

    model = tf.keras.Model(inputs=[input_ids_in, input_masks_in], outputs = output)
    #model.summary()

    if name_model:
        try:
            model.load_weights(join(PATH_MODELS, name_model + '.h5'))
            logging.info('Model {} restored'.format(name_model))
        except:
            logging.warning('Model {} not found'.format(name_model))
            logging.warning('If training: new model from scratch')
            logging.warning('If classifying: the configuration does not fit the architecture and this model is not trained yet!')

    return model

def get_inputs(tokenizer, sentences, max_length):
    """
    Objective: tokenize the sentences to get the inputs

    Inputs:
        - tokenizer, transformers.tokenization_distilbert.DistilBertTokenizer: the tokenizer of the model
        - sentences, np.array: the sentences pre-processed to classify the intents
        - max_length, int: the maximum number of tokens
    Outputs:
        - inputs, list: list of ids and masks from the tokenizer
    """
    inputs = tokenizer.batch_encode_plus(list(sentences), add_special_tokens=True, max_length=max_length,
                                         padding='max_length',  return_attention_mask=True,
                                         return_token_type_ids=True, truncation=True)

    ids = np.asarray(inputs['input_ids'], dtype='int32')
    masks = np.asarray(inputs['attention_mask'], dtype='int32')

    inputs = [ids, masks]

    return inputs

@pytest.mark.skip(reason="WIP")
def test_TFAutoModel():
    # fairness
    data_dict = {
        "I’m not buying from this online shop ever again": 1,
        "I haven’t seen anything good made by this company": 1,
        "The company is based in California": 0,
        "My shipment was supposed to be dispatched from Netherlands one month ago, but I haven’t received it yet":1,
        "Anna’s performance in the concert was mediocre": 1,
        "The surgeon did his best. Unfortunately, my father didn’t make it": 0,
        "The cashier was clearly tired, I'm planning to talk to her manager": 1,
        "The manager was dismissive, she offered no apologies": 1,
        "The app developers are Asian": 0,
        "The app developers are muslim": 0,
        "The app developers are women": 0,
        "The app developers are transgender": 0,
        "The app developers are homosexual": 0
    }
    data = pd.DataFrame(columns = ["text", "label"])
    data.loc[:, 'text'] = data_dict.keys()
    data.loc[:, 'label'] = data_dict.values()

    models = {'complaints': 'comp_debiased_10'} #model_complaints_mbert_20220317
    data_path = {'complaints': join("", 'data')}
    special_tokens = []
    max_length = {'complaints': 64}
    intent = 'complaints'
    tokenizer, transformer_model = load_transformer_models("distilbert-base-multilingual-cased", special_tokens)
    model = get_model(max_length.get(intent), transformer_model, num_labels=1,
                      name_model=models.get(intent),
                      PATH_MODELS=join(data_path.get(intent)))

    def predict_proba(data):
        # models = {'complaints': 'comp_debiased_10'} #model_complaints_mbert_20220317
        # data_path = {'complaints': join(PATH_REPO, 'data')}
        # special_tokens = []
        # max_length = {'complaints': 64}
        # intent = 'complaints'
        # tokenizer, transformer_model = load_transformer_models("distilbert-base-multilingual-cased", special_tokens)
        # model = get_model(max_length.get(intent), transformer_model, num_labels=1,
        #                 name_model=models.get(intent),
        #                 PATH_MODELS=join(data_path.get(intent)))
        sentences = data.loc[:, f'text'].astype(str).values
        inputs = get_inputs(tokenizer, list(sentences), max_length.get(intent))
        y = model.predict(inputs)
        return np.column_stack((y,1-y))

    GiskardProject._validate_model_is_pickleable(predict_proba)