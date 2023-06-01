from typing import Union
from pathlib import Path
import mlflow
import yaml
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset as torch_dataset

from giskard.core.core import SupportedModelTypes
from giskard.core.model import MLFlowBasedModel

# There's no casting currently from str to torch.dtype
str_to_torch_dtype = {
    'torch.float32' : torch.float32,
    'torch.float': torch.float,

    'torch.float64' : torch.float64,
    'torch.double' : torch.double,

    'torch.complex64' : torch.complex64,
    'torch.cfloat' : torch.cfloat,

    'torch.float16' : torch.float16,
    'torch.half': torch.half,

    'torch.bfloat16': torch.bfloat16,

    'torch.uint8': torch.uint8,

    'torch.int8': torch.int8,

    'torch.int16': torch.int16,
    'torch.short': torch.short,

    'torch.int32': torch.int32,
    'torch.int': torch.int,

    'torch.int64': torch.int64,
    'torch.long': torch.long,

    'torch.bool': torch.bool
}


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
        self.torch_dtype = str(torch_dtype)

    @classmethod
    def load_clf(cls, local_dir):
        return mlflow.pytorch.load_model(local_dir)

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.pytorch.save_model(self.clf,
                                  path=local_path,
                                  mlflow_model=mlflow_meta)

    def clf_predict(self, data):
        self.clf.to(self.device)
        self.clf.eval()

        # Use isinstance to check if o is an instance of X or any subclass of X
        # Use is to check if the type of o is exactly X, excluding subclasses of X
        if isinstance(data, pd.DataFrame):
            data = TorchMinimalDataset(data, str_to_torch_dtype[self.torch_dtype])
        elif not isinstance(data, torch_dataset) and not isinstance(data, DataLoader):
            raise Exception(f"The output of data_preprocessing_function is of type={type(data)}.\n \
                            Make sure that your data_preprocessing_function outputs one of the following: \n \
                            - pandas.DataFrame \n \
                            - torch.Dataset \n \
                            - torch.DataLoader")

        predictions = []

        # Figuring out the input shape
        to_unpack = False
        for entry in data:
            # to_unpack = True, for the case of 2 inputs or more, like (input1, offset) or (input1, input2)
            # to_unpack = False, for the case of 1 input
            to_unpack = True if isinstance(entry, tuple) else False
            break

        if to_unpack:
            with torch.no_grad():
                for entry in data:
                    predictions.append(self.clf(*entry).detach().numpy())
        else:
            with torch.no_grad():
                for entry in data:
                    predictions.append(self.clf(entry).detach().numpy())

        predictions = np.squeeze(np.array(predictions))

        if self.model_postprocessing_function:
            predictions = self.model_postprocessing_function(predictions)

        return predictions.squeeze()

    def save_pytorch_meta(self, local_path):
        with open(Path(local_path) / "giskard-model-pytorch-meta.yaml", "w") as f:
            yaml.dump(
                {
                    "device": self.device,
                    "torch_dtype": self.torch_dtype,
                }, f, default_flow_style=False)

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_pytorch_meta(local_path)


    @classmethod
    def load(cls, local_dir, **kwargs):
        pytorch_meta_file = Path(local_dir) / 'giskard-model-pytorch-meta.yaml'
        if pytorch_meta_file.exists():
            with open(pytorch_meta_file) as f:
                pytorch_meta = yaml.load(f, Loader=yaml.Loader)
                kwargs['device'] = pytorch_meta['device']
                kwargs['torch_dtype'] = pytorch_meta['torch_dtype']
                super().load(local_dir, **kwargs)
        else:
            raise ValueError(
                f"Cannot load model ({cls.__module__}.{cls.__name__}), "
                f"{pytorch_meta_file} file not found")
