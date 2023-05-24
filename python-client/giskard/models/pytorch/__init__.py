import collections
import importlib
from pathlib import Path
from typing import Union, Literal, get_args, Optional

import mlflow
import numpy as np
import pandas as pd
import torch
import yaml
import uuid
from torch.utils.data import DataLoader
from torch.utils.data import Dataset as torch_dataset

from giskard.core.core import ModelType
from giskard.models.base import MLFlowBasedModel
from ..utils import map_to_tuples

TorchDType = Literal[
    "float32",
    "float",
    "float64",
    "double",
    "complex64",
    "cfloat",
    "float16",
    "half",
    "bfloat16",
    "uint8",
    "int8",
    "int16",
    "short",
    "int32",
    "int",
    "int64",
    "long",
    "bool",
]


def string_to_torch_dtype(torch_dtype_string: TorchDType):
    try:
        return getattr(importlib.import_module("torch"), torch_dtype_string)
    except AttributeError:
        raise ValueError(
            f"Incorrect torch dtype specified: {torch_dtype_string}, " f"available values are: {get_args(TorchDType)}"
        )


class TorchMinimalDataset(torch_dataset):
    def __init__(self, df: pd.DataFrame, torch_dtype: TorchDType = "float32"):
        self.entries = df
        self.torch_dtype = torch_dtype

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        return torch.tensor(self.entries.iloc[idx].to_numpy(), dtype=string_to_torch_dtype(self.torch_dtype))


class PyTorchModel(MLFlowBasedModel):
    """
    A wrapper class for PyTorch models that extends the functionality of the
    MLFlowBasedModel class.

    Attributes:
        iterate_dataset (bool, optional): Whether to iterate over the dataset for prediction. Defaults to True.
        device (str): The device to run the model on.
        torch_dtype (TorchDType): The data type to be used for input tensors.
    """

    def __init__(
        self,
        model,
        model_type: ModelType,
        torch_dtype: TorchDType = "float32",
        device="cpu",
        name: Optional[str] = None,
        data_preprocessing_function=None,
        model_postprocessing_function=None,
        feature_names=None,
        classification_threshold=0.5,
        classification_labels=None,
        iterate_dataset=True,
        id: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            id=id,
            **kwargs,
        )

        self.device = device
        self.torch_dtype = torch_dtype
        self.iterate_dataset = iterate_dataset

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.pytorch.load_model(local_dir)

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.pytorch.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    def _get_predictions_from_iterable(self, data):
        # Fault tolerance: try to convert to the right format in special cases
        if isinstance(data, pd.DataFrame):
            data = TorchMinimalDataset(data, self.torch_dtype)
        elif isinstance(data, DataLoader):
            data = _get_dataset_from_dataloader(data)

        # Create the data iterator
        try:
            data_iter = iter(data)
        except TypeError as err:
            raise ValueError(
                f"The data exposed to your model must be iterable (instead, we got type={type(data)}). "
                "Make sure that your data or your `data_preprocessing_function` outputs one of the following:\n"
                "- pandas.DataFrame\n- torch.utils.data.Dataset\n- iterable with elements that are compatible with your model"
            ) from err

        try:
            with torch.no_grad():
                return torch.cat([self.model(*entry) for entry in map_to_tuples(data_iter)])
        except ValueError as err:
            raise ValueError(
                "Running your model prediction on one element of your dataset returned an error.\n"
                "Please check that your `data_preprocessing_function` returns an iterable of objects "
                "that are valid inputs for your model."
            ) from err

    def _get_predictions_from_object(self, data):
        try:
            return self.model(data)
        except ValueError as err:
            raise ValueError(
                "Running your model prediction returned an error.\n"
                "Since you specified `iter_dataset=False`, please check that your `data_preprocessing_function` "
                "returns an object that can be passed as input for your model. "
            ) from err

    def model_predict(self, data):
        self.model.to(self.device)
        self.model.eval()

        if self.iterate_dataset:
            predictions = self._get_predictions_from_iterable(data)
        else:
            predictions = self._get_predictions_from_object(data)

        return predictions

    def _convert_to_numpy(self, raw_predictions):
        if isinstance(raw_predictions, torch.Tensor):
            return raw_predictions.detach().numpy()

        return np.asarray(raw_predictions)

    def save_pytorch_meta(self, local_path):
        with open(Path(local_path) / "giskard-model-pytorch-meta.yaml", "w") as f:
            yaml.dump(
                {
                    "device": self.device,
                    "torch_dtype": self.torch_dtype,
                    "iterate_dataset": self.iterate_dataset,
                },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_pytorch_meta(local_path)

    @classmethod
    def load(cls, local_dir, **kwargs):
        pytorch_meta_file = Path(local_dir) / "giskard-model-pytorch-meta.yaml"
        if pytorch_meta_file.exists():
            with open(pytorch_meta_file) as f:
                pytorch_meta = yaml.load(f, Loader=yaml.Loader)
                kwargs["device"] = pytorch_meta["device"]
                kwargs["torch_dtype"] = pytorch_meta["torch_dtype"]
                kwargs["iterate_dataset"] = pytorch_meta.get("iterate_dataset")
                return super().load(local_dir, **kwargs)
        else:
            raise ValueError(
                f"Cannot load model ({cls.__module__}.{cls.__name__}), " f"{pytorch_meta_file} file not found"
            )


def _get_dataset_from_dataloader(dl: DataLoader):
    if not isinstance(dl.dataset, collections.defaultdict):
        return dl.dataset

    raise ValueError(
        f"We tried to infer the torch.utils.data.Dataset from your DataLoader. \n \
                    The type we found was {dl.dataset} which we don't support. Please provide us \n \
                    with a different iterable as output of your data_preprocessing_function."
    )


def _convert_to_numpy(self, predictions):
    return torch.cat(predictions).detach().squeeze(0).numpy()
