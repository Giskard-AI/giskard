"""
2022-12-22 14:20:34.114523: I tensorflow/core/platform/cpu_feature_guard.cc:193] This TensorFlow binary is optimized with oneAPI Deep Neural Network Library (oneDNN) to use the following CPU instructions in performance-critical operations:  AVX2 FMA
To enable them in other operations, rebuild TensorFlow with the appropriate compiler flags.

tests/model_upload/test_TF_cloudpickle_crashes.py:38 (test_tf_cloudpickle)
../giskard/client/project.py:675: in _validate_model_is_pickleable
    pickled_model = cloudpickle.dumps(prediction_function)
../.venv/lib/python3.8/site-packages/cloudpickle/cloudpickle_fast.py:73: in dumps
    cp.dump(obj)
../.venv/lib/python3.8/site-packages/cloudpickle/cloudpickle_fast.py:632: in dump
    return Pickler.dump(self, obj)
../.venv/lib/python3.8/site-packages/keras/engine/training.py:367: in __reduce__
    (pickle_utils.serialize_model_as_bytecode(self),),
../.venv/lib/python3.8/site-packages/keras/saving/pickle_utils.py:73: in serialize_model_as_bytecode
    raise e
../.venv/lib/python3.8/site-packages/keras/saving/pickle_utils.py:69: in serialize_model_as_bytecode
    saving_lib.save_model(model, filepath)
../.venv/lib/python3.8/site-packages/keras/saving/experimental/saving_lib.py:117: in save_model
    serialized_model_dict = serialize_keras_object(model)
../.venv/lib/python3.8/site-packages/keras/saving/experimental/serialization_lib.py:116: in serialize_keras_object
    "config": _get_class_or_fn_config(obj),
../.venv/lib/python3.8/site-packages/keras/saving/experimental/serialization_lib.py:135: in _get_class_or_fn_config
    config = obj.get_config()
../.venv/lib/python3.8/site-packages/keras/engine/functional.py:782: in get_config
    return copy.deepcopy(get_network_config(self, config=config))
../.venv/lib/python3.8/site-packages/keras/engine/functional.py:1564: in get_network_config
    layer_config = serialize_layer_fn(layer)
../.venv/lib/python3.8/site-packages/keras/saving/legacy/serialization.py:330: in serialize_keras_object
    raise e
../.venv/lib/python3.8/site-packages/keras/saving/legacy/serialization.py:324: in serialize_keras_object
    config = instance.get_config()
../.venv/lib/python3.8/site-packages/tensorflow_hub/keras_layer.py:329: in get_config
    raise NotImplementedError(
E   NotImplementedError: Can only generate a valid config for `hub.KerasLayer(handle, ...)`that uses a string `handle`.
E
E   Got `type(handle)`: <class 'tensorflow_hub.keras_layer.KerasLayer'>

During handling of the above exception, another exception occurred:
model_upload/test_TF_cloudpickle_crashes.py:138: in test_tf_cloudpickle
    GiskardProject._validate_model_is_pickleable(classifier_model)
../giskard/client/project.py:678: in _validate_model_is_pickleable
    raise ValueError("Unable to pickle or unpickle model on Giskard")
E   ValueError: Unable to pickle or unpickle model on Giskard
"""
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from string import punctuation
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
from official.nlp import optimization  # to create AdamW optimizer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.compose import ColumnTransformer
from sklearn import model_selection

from giskard.client.project import GiskardProject

def test_tf_cloudpickle():

    column_types={
        'Target': "category",
        "Subject": "text",
        "Content": "text",
        "Week_day": "category",
        "Month": "category",
        "Hour": "numeric",
        "Nb_of_forwarded_msg": "numeric",
        "Year": "numeric",
    }

    data_filtered = pd.read_csv('/Users/rak/Documents/model-API/errors/error-scripts/temp.csv')
    stoplist = set(stopwords.words('english') + list(punctuation))
    stemmer = PorterStemmer()
    text_transformer = Pipeline([
        ('vect', CountVectorizer(stop_words=stoplist)),
        ('tfidf', TfidfTransformer())
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ('text_Mail', text_transformer, "Content")
        ]
    )

    feature_types = {i:column_types[i] for i in column_types if i!="Target"}
    Y = data_filtered["Target"]
    X = data_filtered.drop(columns=["Target"])
    X_train,X_test,Y_train,Y_test = model_selection.train_test_split(X, Y,test_size=0.20, random_state = 30, stratify = Y)

    #=======================================================================================

    classification_labels_mapping = {'REGULATION': 0,'INTERNAL': 1,'CALIFORNIA CRISIS': 2,'INFLUENCE': 3}

    Y = data_filtered['Target'].map(classification_labels_mapping)
    X = data_filtered['Content']
    X_train,X_test,Y_train,Y_test = model_selection.train_test_split(X, Y,test_size=0.20, random_state = 30, stratify = Y)


    from tensorflow.keras.utils import to_categorical
    Y_train = to_categorical(Y_train)
    Y_test = to_categorical(Y_test)

    tfhub_handle_preprocess = hub.load("https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")


    #tfhub_handle_encoder = 'https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-4_H-512_A-8/1'
    #tfhub_handle_preprocess = 'https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3'
    tfhub_handle_preprocess = hub.KerasLayer(
        "https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3")
    tfhub_handle_encoder = hub.KerasLayer(
        "https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-128_A-2/2",
        trainable=True)

    def build_classifier_model():

        text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
        preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess, name='preprocessing')
        encoder_inputs = preprocessing_layer(text_input)
        encoder = hub.KerasLayer(tfhub_handle_encoder, trainable=True, name='BERT_encoder')
        outputs = encoder(encoder_inputs)
        net = outputs['pooled_output']
        net = tf.keras.layers.Dropout(0.1)(net)
        net = tf.keras.layers.Dense(4, activation='softmax', name='classifier')(net)
        return tf.keras.Model(inputs=text_input, outputs=net)


    dataset = tf.data.Dataset.from_tensor_slices((X, Y))

    classifier_model = build_classifier_model()
    loss = tf.keras.losses.BinaryCrossentropy(from_logits=False)
    metrics = tf.metrics.BinaryAccuracy()

    epochs = 1
    steps_per_epoch = tf.data.experimental.cardinality(dataset).numpy()
    num_train_steps = steps_per_epoch * epochs
    num_warmup_steps = int(0.1*num_train_steps)

    init_lr = 3e-5
    optimizer = optimization.create_optimizer(init_lr=init_lr,
                                              num_train_steps=num_train_steps,
                                              num_warmup_steps=num_warmup_steps,
                                              optimizer_type='adamw')

    classifier_model.compile(optimizer=optimizer,
                             loss=loss,
                             metrics=metrics)

    print(f'Training model with {tfhub_handle_encoder}')
    history = classifier_model.fit(X_train, Y_train,
                                   epochs=epochs)


    loss, accuracy = classifier_model.evaluate(X_test,Y_test)

    print(f'Loss: {loss}')
    print(f'Accuracy: {accuracy}')

    GiskardProject._validate_model_is_pickleable(classifier_model)
    GiskardProject._validate_model_is_pickleable(classifier_model.predict)