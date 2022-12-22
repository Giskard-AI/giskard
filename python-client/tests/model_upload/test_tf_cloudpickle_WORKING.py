import os

import tensorflow as tf
from tensorflow import keras
from giskard.client.project import GiskardProject

# Define a simple sequential model
def create_model():
    model = tf.keras.Sequential([
        keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(10)
    ])

    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])

    return model


def test_tf_cloudpickle():

    # Create a basic model instance
    model = create_model()

    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()

    train_labels = train_labels[:100]
    #test_labels = test_labels[:100]

    train_images = train_images[:100].reshape(-1, 28 * 28) / 255.0
    #test_images = test_images[:100].reshape(-1, 28 * 28) / 255.0

    # Create and train a new model instance.
    model = create_model()
    model.fit(train_images, train_labels, epochs=5)

    # Save the entire model as a SavedModel.
    #os.system('mkdir -p saved_model')
    #model.save('saved_model/my_model')

    GiskardProject._validate_model_is_pickleable(model)