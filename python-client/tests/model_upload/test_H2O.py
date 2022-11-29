import httpretty
gsk_url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "multipart/form-data; boundary="
model_name = "uploaded model"
b_content_type = b"application/json"

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

@httpretty.activate(verbose=True, allow_net_connect=False)
def test_upload_H2O():
    httpretty.register_uri(httpretty.POST, "http://giskard-host:12345/api/v2/project/models/upload")
    client = GiskardClient(gsk_url, token)
    project = GiskardProject(client.session, "test-project", 1)
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

    project.upload_model(
        prediction_function=prediction_function, #aml.leader.predict,
        model_type='classification',
        target = 'went_on_backorder',
        feature_names=['national_inv','lead_time','in_transit_qty','forecast_3_month','forecast_6_month','forecast_9_month','sales_1_month','sales_3_month',
                       'sales_6_month','sales_9_month','min_bank','potential_issue','pieces_past_due','perf_6_month_avg','perf_12_month_avg','local_bo_qty','deck_risk',
                       'oe_constraint','ppap_risk','stop_auto_buy','rev_stop'],
        classification_labels=['Yes','No'])