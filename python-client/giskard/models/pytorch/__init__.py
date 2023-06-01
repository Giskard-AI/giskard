import mlflow
import torch
from torch.utils.data import Dataset as torch_dataset
from torch.utils.data import DataLoader
from pathlib import Path
import yaml
from typing import Union
import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model
from giskard.path_utils import get_size
class TorchMinimalDataset(torch_dataset):
    def __init__(self, df: pd.DataFrame):
        self.entries = df

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        return self.entries.iloc[idx]


class PyTorchModel(Model):
    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 device='cpu',
                 name: str = None,
                 data_preprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None,
                 loader_module:str = 'giskard.models.pytorch',
                 loader_class:str = 'PyTorchModel') -> None:

        super().__init__(clf, model_type, name, data_preprocessing_function, feature_names,
                         classification_threshold, classification_labels, loader_module, loader_class)
        self.device=device

    @classmethod
    def read_model_from_local_dir(cls, local_path):
        return mlflow.pytorch.load_model(local_path)


    def save_to_local_dir(self, local_path):

        info = self._new_mlflow_model_meta()
        mlflow.pytorch.save_model(self.clf,
                                  path=local_path,
                                  mlflow_model=info)
        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
            yaml.dump(
                {
                    "language_version": info.flavors['python_function']['python_version'],
                    "loader_module": self.meta.loader_module,
                    "loader_class": self.meta.loader_class,
                    "language": "PYTHON",
                    "model_type": self.meta.model_type.name.upper(),
                    "threshold": self.meta.classification_threshold,
                    "feature_names": self.meta.feature_names,
                    "classification_labels": self.meta.classification_labels,
                    "id": info.model_uuid,
                    "name": self.meta.name,
                    "size": get_size(local_path),
                }, f, default_flow_style=False)

        return info

    def _raw_predict(self, data):
        self.clf.to(self.device)
        self.clf.eval()

        # Use isinstance to check if o is an instance of X or any subclass of X
        # Use is to check if the type of o is exactly X, excluding subclasses of X
        with torch.no_grad():
            if isinstance(data, tuple):
                predictions = self.clf(*data)
            elif isinstance(data, dict):
                predictions = self.clf(**data)
            elif isinstance(data, pd.DataFrame):
                dataset = TorchMinimalDataset(data)
                data_loader = DataLoader(dataset)
                predictions=[]
                for data_entry in data_loader:
                    predictions.append(self.clf(data_entry).detach().numpy())
            elif isinstance(data, torch_dataset):
                data_loader = DataLoader(dataset)
                predictions=[]
                for data_entry in data_loader:
                    predictions.append(self.clf(data_entry).detach().numpy())
            else:
                predictions = self.clf(data)

        if self.is_classification:
            with torch.no_grad():
                predictions = torch.nn.functional.softmax(predictions, dim=-1)

        predictions = np.array(predictions)
        return predictions




