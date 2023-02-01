"""
Issue :https://github.com/Giskard-AI/giskard/issues/374
Error:
# ../giskard/client/project.py:676: in _validate_model_is_pickleable
#     unpickled_model = cloudpickle.loads(pickled_model)
# E   TypeError: __new__() missing 1 required positional argument: 'keyvals'
"""


from giskard.client.project import GiskardProject
import h2o
from h2o.automl import H2OAutoML
import os
import pytest

@pytest.mark.skip(reason="Will be solved in the new API: https://github.com/Giskard-AI/giskard/pull/618")
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