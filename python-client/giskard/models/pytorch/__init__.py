import collections
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import yaml

import mlflow
from giskard.core.core import ModelType
from giskard.models.base import MLFlowBasedModel
from ..utils import map_to_tuples

try:
    import torch
    from torch.utils.data import DataLoader
    from torch.utils.data import Dataset as torch_dataset
except ImportError:
    pass

# There's no casting currently from str to torch.dtype
str_to_torch_dtype = {
    "torch.float32": torch.float32,
    "torch.float": torch.float,
    "torch.float64": torch.float64,
    "torch.double": torch.double,
    "torch.complex64": torch.complex64,
    "torch.cfloat": torch.cfloat,
    "torch.float16": torch.float16,
    "torch.half": torch.half,
    "torch.bfloat16": torch.bfloat16,
    "torch.uint8": torch.uint8,
    "torch.int8": torch.int8,
    "torch.int16": torch.int16,
    "torch.short": torch.short,
    "torch.int32": torch.int32,
    "torch.int": torch.int,
    "torch.int64": torch.int64,
    "torch.long": torch.long,
    "torch.bool": torch.bool,
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
    def __init__(
            self,
            clf,
            model_type: ModelType,
            torch_dtype=torch.float32,
            device="cpu",
            name: str = None,
            data_preprocessing_function=None,
            model_postprocessing_function=None,
            feature_names=None,
            classification_threshold=0.5,
            classification_labels=None,
            iterate_dataset=True,
    ) -> None:
        super().__init__(
            clf=clf,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

        self.device = device
        self.torch_dtype = str(torch_dtype)
        self.iterate_dataset = iterate_dataset

    @classmethod
    def load_clf(cls, local_dir):
        return mlflow.pytorch.load_model(local_dir)

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.pytorch.save_model(self.clf, path=local_path, mlflow_model=mlflow_meta)

    def _get_predictions_from_iterable(self, data):
        # Fault tolerance: try to convert to the right format in special cases
        if isinstance(data, pd.DataFrame):
            data = TorchMinimalDataset(data, str_to_torch_dtype[self.torch_dtype])
        elif isinstance(data, DataLoader):
            data = _get_dataset_from_dataloader(data)

        # Create the data iterator
        try:
            data_iter = iter(data)
        except TypeError as err:
            raise ValueError(
                f"The data exposed to your clf must be iterable (instead, we got type={type(data)}). "
                "Make sure that your data or your `data_preprocessing_function` outputs one of the following:\n"
                "- pandas.DataFrame\n- torch.utils.data.Dataset\n- iterable with elements that are compatible with your clf"
            ) from err

        try:
            with torch.no_grad():
                return torch.cat([self.clf(*entry) for entry in map_to_tuples(data_iter)])
        except ValueError as err:
            raise ValueError(
                "Running your model prediction on one element of your dataset returned an error.\n"
                "Please check that your `data_preprocessing_function` returns an iterable of objects "
                "that are valid inputs for your model."
            ) from err

    def _get_predictions_from_object(self, data):
        try:
            return self.clf(data)
        except ValueError as err:
            raise ValueError(
                "Running your model prediction returned an error.\n"
                "Since you specified `iter_dataset=False`, please check that your `data_preprocessing_function` "
                "returns an object that can be passed as input for your model. "
            ) from err

    def clf_predict(self, data):
        self.clf.to(self.device)
        self.clf.eval()

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
