from typing import Union

import mlflow
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset as torch_dataset

from giskard.core.core import SupportedModelTypes
from giskard.core.model import MLFlowBasedModel


class TorchMinimalDataset(torch_dataset):
    def __init__(self, df: pd.DataFrame, torch_dtype=torch.float32):
        self.entries = df
        self.torch_dtype = torch_dtype

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        return torch.tensor(self.entries.iloc[idx].to_numpy(), dtype=self.torch_dtype)


class PyTorchModel(MLFlowBasedModel):

    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 torch_dtype=torch.float32,
                 device='cpu',
                 name: str = None,
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        super().__init__(clf=clf,
                         model_type=model_type,
                         name=name,
                         data_preprocessing_function=data_preprocessing_function,
                         model_postprocessing_function=model_postprocessing_function,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)

        self.device = device
        self.torch_dtype = torch_dtype

    @classmethod
    def read_model_from_local_dir(cls, local_path):
        return mlflow.pytorch.load_model(local_path)

    def save_with_mflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.pytorch.save_model(self.clf,
                                  path=local_path,
                                  mlflow_model=mlflow_meta)

    def clf_predict(self, data):
        self.clf.to(self.device)
        self.clf.eval()

        # Use isinstance to check if o is an instance of X or any subclass of X
        # Use is to check if the type of o is exactly X, excluding subclasses of X
        if isinstance(data, pd.DataFrame):
            data = TorchMinimalDataset(data, self.torch_dtype)
        elif not isinstance(data, torch_dataset) and not isinstance(data, DataLoader):
            raise Exception(f"The output of data_preprocessing_function is of type={type(data)}.\n \
                            Make sure that your data_preprocessing_function outputs one of the following: \n \
                            - pandas.DataFrame \n \
                            - torch.Dataset \n \
                            - torch.DataLoader")

        predictions = []
        with torch.no_grad():
            for entry in data:
                try:  # for the case of 1 input
                    predictions.append(self.clf(entry).detach().numpy())
                except:  # for the case of 2 inputs or more, like (input1, offset) or (input1, input2)
                    predictions.append(self.clf(*entry).detach().numpy())

        predictions = np.squeeze(np.array(predictions))

        if self.model_postprocessing_function:
            predictions = self.model_postprocessing_function(predictions)

        return predictions.squeeze()
