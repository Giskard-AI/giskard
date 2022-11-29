import os
import shutil
import tensorflow as tf
import pandas as pd
from tensorflow.keras import layers
import pytest

## initiate Giskard project
from giskard.client.giskard_client import GiskardClient
from giskard.client.project import GiskardProject

import h2o
from h2o.automl import H2OAutoML
import os

#@pytest.mark.skip(reason="GSK-388 H2O models unable to unpickle on Giskard")
def test_upload_H2O():

    h2o.init()

    aml = H2OAutoML(max_models = 1, seed = 1)
    # Use local data file or download from GitHub
    docker_data_path = "/home/h2o/data/automl/product_backorders.csv"
    if os.path.isfile(docker_data_path):
        data_path = docker_data_path
    else:
        data_path = "https://github.com/h2oai/h2o-tutorials/raw/master/h2o-world-2017/automl/data/product_backorders.csv"

    # Load data into H2O
    df = h2o.import_file(data_path)
    y = "went_on_backorder"
    x = df.columns
    aml.train(x = x, y = y, training_frame = df)

    def prediction_function(df):
        preds = aml.leader.predict(test_data=df)
        preds = np.array(preds.as_data_frame()[['Yes','No']])
        return preds

    GiskardProject._validate_model_is_pickleable(prediction_function)