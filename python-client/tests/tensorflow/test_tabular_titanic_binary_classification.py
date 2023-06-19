import joblib
import pandas as pd
import pytest
from huggingface_hub import hf_hub_url, cached_download
from tensorflow.keras.models import load_model

import tests.utils
from giskard import Dataset
from giskard.models.tensorflow import TensorFlowModel


@pytest.mark.skip(reason="it uses uncompatible version of scikit-learn==1.1.1")
def test_tabular_titanic_binary_classification():
    REPO_ID = "danupurnomo/dummy-titanic"
    PIPELINE_FILENAME = "final_pipeline.pkl"
    TF_FILENAME = "titanic_model.h5"

    model_pipeline = joblib.load(cached_download(hf_hub_url(REPO_ID, PIPELINE_FILENAME)))

    model_seq = load_model(cached_download(hf_hub_url(REPO_ID, TF_FILENAME)))

    new_data = {
        "PassengerId": 1191,
        "Pclass": 1,
        "Name": "Sherlock Holmes",
        "Sex": "male",
        "Age": 30,
        "SibSp": 0,
        "Parch": 0,
        "Ticket": "C.A.29395",
        "Fare": 12,
        "Cabin": "F44",
        "Embarked": "S",
    }
    new_data = pd.DataFrame([new_data, new_data])

    def my_preproccessing_function(df):
        return model_pipeline.transform(df)

    my_model = TensorFlowModel(
        name=TF_FILENAME,
        model=model_seq,
        feature_names=list(new_data.keys()),
        model_type="classification",
        classification_labels=["0", "1"],
        data_preprocessing_function=my_preproccessing_function,
    )

    my_test_dataset = Dataset(new_data, name="test dataset")

    tests.utils.verify_model_upload(my_model, my_test_dataset)
