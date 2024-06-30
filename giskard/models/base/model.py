from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Type, Union

import builtins
import importlib
import json
import logging
import platform
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd
import yaml

from giskard.client.dtos import ModelMetaInfo
from giskard.core.errors import GiskardInstallationError

from ...core.core import ModelMeta, ModelType, SupportedModelTypes
from ...core.validation import configured_validate_arguments
from ...datasets.base import Dataset
from ...exceptions.giskard_exception import python_env_exception_helper
from ...models.cache import ModelCache
from ...path_utils import get_size
from ...registry.utils import dump_by_value
from ...utils.logging_utils import Timer
from ..cache import get_cache_enabled
from ..utils import np_types_to_native
from .model_prediction import ModelPredictionResults

if TYPE_CHECKING:
    from ...scanner.report import ScanReport

META_FILENAME = "giskard-model-meta.yaml"

MODEL_CLASS_PKL = "ModelClass.pkl"

logger = logging.getLogger(__name__)


def _validate_text_generation_params(name, description, feature_names):
    if not name or not description:
        raise ValueError(
            "The parameters 'name' and 'description' are required for 'text_generation' models, please make sure you "
            "pass them when wrapping your model. Both are very important in order for the LLM-assisted testing and "
            "scan to work properly. Name and description should briefly describe the expected behavior of your model. "
            "Check our documentation for more information."
        )

    if not feature_names:
        raise ValueError(
            "The parameter 'feature_names' is required for 'text_generation' models. It is a list of the input "
            "variables for your model, e.g. ['question', 'user_language']. Please make sure to set this parameter "
            "when wrapping your model."
        )


class BaseModel(ABC):
    """
    The BaseModel class is an abstract base class that defines the common interface for all the models used in this project.

    Attributes:
       model (Any):
            Could be any function or ML model. The standard model output required for Giskard is:

            * if classification:
                an array (nxm) of probabilities corresponding to n data entries (rows of pandas.DataFrame)
                and m classification_labels. In the case of binary classification, an array of (nx1) probabilities is
                also accepted.
                Make sure that the probability provided is for the second label provided in classification_labels.
            * if regression or text_generation:
                an array of predictions corresponding to data entries
                (rows of pandas.DataFrame) and outputs.

       name (Optional[str]):
            the name of the model.
       model_type (ModelType):
           The type of the model: regression, classification or text_generation.
       feature_names (Optional[Iterable[str]]):
           list of feature names matching the column names in the data that correspond to the features which the model
           trained on. By default, feature_names are all the Dataset columns except from target.
       classification_threshold (float):
           represents the classification model threshold, for binary
           classification models.
       classification_labels (Optional[Iterable[str]]):
           that represents the classification labels, if model_type is
           classification. Make sure the labels have the same order as the column output of clf.

    Raises:
        ValueError
            If an invalid model type is specified.
            If duplicate values are found in the classification_labels.
    """

    should_save_model_class = False
    id: uuid.UUID
    _cache: ModelCache

    @configured_validate_arguments
    def __init__(
        self,
        model_type: ModelType,
        name: Optional[str] = None,
        description: Optional[str] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize a new instance of the BaseModel class.

        Parameters:
            model_type (ModelType): Type of the model, either ModelType.REGRESSION or ModelType.CLASSIFICATION.
            name (Optional[str]): Name of the model. If not provided, defaults to the class name.
            description (Optional[str]): Description of the model's task. Mandatory for non-langchain text_generation models.
            feature_names (Optional[Iterable]): A list of names of the input features.
            classification_threshold (Optional[float]): Threshold value used for classification models. Defaults to 0.5.
            classification_labels (Optional[Iterable]): A list of labels for classification models.

        Raises:
            ValueError: If an invalid model_type value is provided.
            ValueError: If duplicate values are found in the classification_labels list.

        Notes:
            This class uses the @configured_validate_arguments decorator to validate the input arguments.
            The initialized object contains the following attributes:

            - meta: a ModelMeta object containing metadata about the model.

        """
        self.id = uuid.UUID(id) if id is not None else uuid.UUID(kwargs.get("id", uuid.uuid4().hex))
        if isinstance(model_type, str):
            try:
                model_type = SupportedModelTypes(model_type)
            except ValueError as e:
                available_values = {i.value for i in SupportedModelTypes}
                raise ValueError(
                    f'Invalid model type value "{model_type}". Available values are: {available_values}'
                ) from e

        if classification_labels is not None:
            classification_labels = list(classification_labels)
            if len(classification_labels) != len(set(classification_labels)):
                raise ValueError("Duplicates are found in 'classification_labels', please only provide unique values.")

        self._cache = ModelCache(
            model_type,
            str(self.id),
            persist_cache=kwargs.get("persist_cache", False),
            cache_dir=kwargs.get("prediction_cache_dir"),
        )

        # sklearn and catboost will fill classification_labels before this check
        if model_type == SupportedModelTypes.CLASSIFICATION and not classification_labels:
            raise ValueError("The parameter 'classification_labels' is required if 'model_type' is 'classification'.")

        if model_type == SupportedModelTypes.TEXT_GENERATION:
            _validate_text_generation_params(name, description, feature_names)

        self.meta = ModelMeta(
            name=name if name is not None else self.__class__.__name__,
            description=description if description is not None else "No description",
            model_type=model_type,
            feature_names=list(feature_names) if feature_names is not None else None,
            classification_labels=np_types_to_native(classification_labels),
            loader_class=self.__class__.__name__,
            loader_module=self.__module__,
            classification_threshold=classification_threshold,
        )

    @property
    def name(self):
        return self.meta.name if self.meta.name is not None else self.__class__.__name__

    @property
    def description(self):
        return self.meta.description

    @property
    def model_type(self):
        return self.meta.model_type

    @property
    def feature_names(self):
        return self.meta.feature_names

    @property
    def classification_labels(self):
        return self.meta.classification_labels

    @property
    def loader_class(self):
        return self.meta.loader_class

    @property
    def loader_module(self):
        return self.meta.loader_module

    @property
    def classification_threshold(self):
        return self.meta.classification_threshold

    @property
    def is_classification(self) -> bool:
        """Compute if the model is of type classification.

        Returns:
            bool: True if the model is of type classification, False otherwise
        """
        return self.model_type == SupportedModelTypes.CLASSIFICATION

    @property
    def is_binary_classification(self) -> bool:
        """Compute if the model is of type binary classification.

        Returns:
            bool: True if the model is of type binary classification, False otherwise.
        """

        return self.is_classification and len(self.classification_labels) == 2

    @property
    def is_regression(self) -> bool:
        """Compute if the model is of type regression.

        Returns:
            bool: True if the model is of type regression, False otherwise.
        """
        return self.model_type == SupportedModelTypes.REGRESSION

    @property
    def is_text_generation(self) -> bool:
        """Compute if the model is of type text generation.

        Returns:
            bool: True if the model is of type text generation, False otherwise.
        """
        return self.model_type == SupportedModelTypes.TEXT_GENERATION

    @classmethod
    def get_model_class(cls, class_file: Path, model_py_ver: Optional[Tuple[str, str, str]] = None):
        with open(class_file, "rb") as f:
            try:
                # According to https://github.com/cloudpipe/cloudpickle#cloudpickle:
                # Cloudpickle can only be used to send objects between the exact same version of Python.
                clazz = cloudpickle.load(f)
            except Exception as e:
                raise python_env_exception_helper(cls.__name__, e, required_py_ver=model_py_ver)
            if not issubclass(clazz, BaseModel):
                raise ValueError(f"Unknown model class: {clazz}. Models should inherit from 'BaseModel' class")
            return clazz

    @classmethod
    def determine_model_class(
        cls, meta, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *_args, **_kwargs
    ):
        class_file = Path(local_dir) / MODEL_CLASS_PKL
        if class_file.exists():
            return cls.get_model_class(class_file, model_py_ver)
        else:
            return getattr(importlib.import_module(meta.loader_module), meta.loader_class)

    def save_meta(self, local_path, *_args, **_kwargs):
        with (Path(local_path) / META_FILENAME).open(mode="w", encoding="utf-8") as f:
            yaml.dump(
                {
                    "language_version": platform.python_version(),
                    "language": "PYTHON",
                    "model_type": self.model_type.name.upper(),
                    "threshold": self.classification_threshold,
                    "feature_names": self.feature_names,
                    "classification_labels": self.classification_labels,
                    "loader_module": self.loader_module,
                    "loader_class": self.loader_class,
                    "id": str(self.id),
                    "name": self.name,
                    "description": self.description,
                    "size": get_size(local_path),
                },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path], *_args, **_kwargs) -> None:
        if self.should_save_model_class:
            self.save_model_class(local_path)
        self.save_meta(local_path)

    def save_model_class(self, local_path, *_args, **_kwargs):
        class_file = Path(local_path) / MODEL_CLASS_PKL
        with open(class_file, "wb") as f:
            dump_by_value(self.__class__, f)

    def prepare_dataframe(self, df, column_dtypes=None, target=None, *_args, **_kwargs):
        """
        Prepares a Pandas DataFrame for inference by ensuring the correct columns are present and have the correct data types.

        Args:
            dataset (Dataset): The dataset to prepare.

        Returns:
            pd.DataFrame: The prepared Pandas DataFrame.

        Raises:
            ValueError: If the target column is found in the dataset.
            ValueError: If a specified feature name is not found in the dataset.
        """
        df = df.copy()
        column_dtypes = dict(column_dtypes) if column_dtypes else None

        if column_dtypes:
            for cname, ctype in column_dtypes.items():
                if cname not in df:
                    df[cname] = np.nan

        if target:
            if target in df.columns:
                df.drop(target, axis=1, inplace=True)
            if column_dtypes and target in column_dtypes:
                del column_dtypes[target]
            if target and self.feature_names and target in self.feature_names:
                self.feature_names.remove(target)

        if self.feature_names:
            if set(self.feature_names) > set(df.columns):
                column_names = set(self.feature_names) - set(df.columns)
                raise ValueError(
                    f"The following columns are not found in the dataset: {', '.join(sorted(column_names))}"
                )
            df = df[self.feature_names]
            if column_dtypes:
                column_dtypes = {k: v for k, v in column_dtypes.items() if k in self.feature_names}

        for cname, ctype in column_dtypes.items():
            if cname not in df:
                df[cname] = np.nan

        if column_dtypes:
            df = Dataset.cast_column_to_dtypes(df, column_dtypes)
        return df

    def predict(self, dataset: Dataset, *_args, **_kwargs) -> ModelPredictionResults:
        """Generates predictions for the input giskard dataset.
        This method uses the `prepare_dataframe()` method to preprocess the input dataset before making predictions.
        The `predict_df()` method is used to generate raw predictions for the preprocessed data.
        The type of predictions generated by this method depends on the model type:

        * For regression models, the `prediction` field of the returned `ModelPredictionResults` object will contain the same
            values as the `raw_prediction` field.
        * For binary or multiclass classification models, the `prediction` field of the returned `ModelPredictionResults` object
            will contain the predicted class labels for each example in the input dataset.
            The `probabilities` field will contain the predicted probabilities for the predicted class label.
            The `all_predictions` field will contain the predicted probabilities for all class labels for each example in the input dataset.


        Args:
            dataset (Dataset): The input dataset to make predictions on.

        Raises:
            ValueError: If the prediction task is not supported by the model.

        Returns:
            ModelPredictionResults: The prediction results for the input dataset.
        """
        if not len(dataset.df):
            return ModelPredictionResults()
        timer = Timer()

        if get_cache_enabled():
            raw_prediction = self._predict_from_cache(dataset)
        else:
            raw_prediction = self.predict_df(
                self.prepare_dataframe(dataset.df, column_dtypes=dataset.column_dtypes, target=dataset.target)
            )

        if self.is_regression or self.is_text_generation:
            result = ModelPredictionResults(
                prediction=raw_prediction, raw_prediction=raw_prediction, raw=raw_prediction
            )
        elif self.is_classification:
            labels = np.array(self.classification_labels)
            threshold = self.classification_threshold

            if threshold is not None and len(labels) == 2:
                predicted_lbl_idx = (raw_prediction[:, 1] > threshold).astype(int)
            else:
                predicted_lbl_idx = raw_prediction.argmax(axis=1)

            all_predictions = pd.DataFrame(raw_prediction, columns=labels)

            predicted_labels = labels[predicted_lbl_idx]
            probability = raw_prediction[range(len(predicted_lbl_idx)), predicted_lbl_idx]

            result = ModelPredictionResults(
                raw=raw_prediction,
                prediction=predicted_labels,
                raw_prediction=predicted_lbl_idx,
                probabilities=probability,
                all_predictions=all_predictions,
            )
        else:
            raise ValueError(f"Prediction task is not supported: {self.model_type}")
        timer.stop(f"Predicted dataset with shape {dataset.df.shape}")
        return result

    @abstractmethod
    def predict_df(self, df: pd.DataFrame, *args, **kwargs):
        """
        Inner method that does the actual inference of a prepared dataframe
        :param df: dataframe to predict
        """
        ...

    def _predict_from_cache(self, dataset: Dataset):
        cached_predictions = self._cache.read_from_cache(dataset.row_hashes)
        missing = cached_predictions.isna()

        missing_slice = dataset.slice(lambda x: dataset.df[missing], row_level=False)
        unpredicted_df = self.prepare_dataframe(
            missing_slice.df, column_dtypes=missing_slice.column_dtypes, target=missing_slice.target
        )

        if len(unpredicted_df) > 0:
            raw_prediction = self.predict_df(unpredicted_df)
            self._cache.set_cache(dataset.row_hashes[missing], raw_prediction)
            cached_predictions.loc[missing] = raw_prediction.tolist()

        # TODO: check if there is a better solution
        return np.array(np.array(cached_predictions).tolist())

    @classmethod
    def read_meta_from_local_dir(cls, local_dir, *_args, **_kwargs) -> Tuple[ModelMetaInfo, ModelMeta]:
        with (Path(local_dir) / META_FILENAME).open(encoding="utf-8") as f:
            file_meta = yaml.load(f, Loader=yaml.Loader)
            meta = ModelMeta(
                name=file_meta["name"],
                description=None if "description" not in file_meta else file_meta["description"],
                model_type=SupportedModelTypes[file_meta["model_type"]],
                feature_names=file_meta["feature_names"],
                classification_labels=file_meta["classification_labels"],
                classification_threshold=file_meta["threshold"],
                loader_module=file_meta["loader_module"],
                loader_class=file_meta["loader_class"],
            )

            # Bring more information, such as language and language version
            extra_meta = ModelMetaInfo(
                id=file_meta["id"],
                name=meta.name,
                modelType=file_meta["model_type"],
                featureNames=meta.feature_names if meta.feature_names is not None else [],
                threshold=meta.classification_threshold,
                description=meta.description,
                classificationLabels=meta.classification_labels
                if meta.classification_labels is None
                else list(map(str, meta.classification_labels)),
                languageVersion=file_meta["language_version"],
                language=file_meta["language"],
                size=file_meta["size"],
                classificationLabelsDtype=None,
                createdDate="",
                projectId=-1,
            )
        return extra_meta, meta

    @classmethod
    def cast_labels(cls, meta_response: ModelMetaInfo, *_args, **_kwargs) -> List[Union[str, Type]]:
        labels_ = meta_response.classificationLabels
        labels_dtype = meta_response.classificationLabelsDtype
        if labels_ and labels_dtype and builtins.hasattr(builtins, labels_dtype):
            dtype = builtins.getattr(builtins, labels_dtype)
            labels_ = [dtype(i) for i in labels_]
        return labels_

    @classmethod
    def load(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *_args, **kwargs):
        class_file = Path(local_dir) / MODEL_CLASS_PKL
        model_meta_info, meta = cls.read_meta_from_local_dir(local_dir)

        constructor_params = meta.__dict__
        constructor_params["id"] = model_meta_info.id
        del constructor_params["loader_module"]
        del constructor_params["loader_class"]

        if class_file.exists():
            with open(class_file, "rb") as f:
                try:
                    # According to https://github.com/cloudpipe/cloudpickle#cloudpickle:
                    # Cloudpickle can only be used to send objects between the exact same version of Python.
                    clazz = cloudpickle.load(f)
                except Exception as e:
                    raise python_env_exception_helper(cls.__name__, e, required_py_ver=model_py_ver)
                clazz_kwargs = {}
                clazz_kwargs.update(constructor_params)
                clazz_kwargs.update(kwargs)
                return clazz(**clazz_kwargs)
        else:
            raise ValueError(
                f"Cannot load model ({cls.__module__}.{cls.__name__}), "
                f"{MODEL_CLASS_PKL} file not found and 'load' method isn't overriden"
            )

    def to_mlflow(self, *_args, **_kwargs):
        raise NotImplementedError()

    def __str__(self) -> str:
        if self.name:  # handle both None and empty string
            return f"{self.name}({self.id})"
        return super().__str__()  # default to `<giskard.models.base.Model object at ...>`

    def _get_available_tools(self, dataset: Dataset, scan_report: ScanReport) -> dict:
        """Get the dictionary with available tools.

        Parameters
        ----------
        dataset : Dataset
            Giskard Dataset to be analysed by Tools.
        scan_report : ScanReport
            Giskard Scan Report to be analysed by Tools.

        Returns
        -------
        dict[str, BaseTool]
            The dictionary with Tools' names and related instances.
        """
        try:
            from ...llm.talk.tools import (
                IssuesScannerTool,
                MetricTool,
                PredictTool,
                SHAPExplanationTool,
            )
        except ImportError as err:
            raise GiskardInstallationError(flavor="talk") from err

        return {
            PredictTool.default_name: PredictTool(model=self, dataset=dataset),
            MetricTool.default_name: MetricTool(model=self, dataset=dataset),
            SHAPExplanationTool.default_name: SHAPExplanationTool(model=self, dataset=dataset),
            IssuesScannerTool.default_name: IssuesScannerTool(scan_report=scan_report),
        }

    @staticmethod
    def _gather_context(message_list: list) -> str:
        """Gather context into a single string.

        Given the list of OpenAI's messages, extracts and joins their contents into a single string.

        Parameters
        ----------
        message_list : list
            The list of OpenAI's messages.

        Returns
        -------
        str
            The string with the joined messages' contents.
        """
        return "\n".join([json.dumps(asdict(msg)) for msg in message_list])

    def talk(self, question: str, dataset: Dataset, scan_report: ScanReport = None, context: str = ""):
        """Perform the 'talk' to the model.

        Given `question`, allows to ask the model about prediction result, explanation, model performance, issues, etc.

        Parameters
        ----------
        question : str
            User input query.
        dataset : Dataset
            Giskard Dataset to be analysed by the 'talk'.
        context : str
            Context of the previous 'talk' results. Necessary to keep context between sequential 'talk' calls.
        scan_report : ScanReport
            Giskard Scan Report to be analysed by the 'talk'.

        Returns
        -------
        TalkResult
            The response for the user's prompt.
        """
        try:
            from ...llm.client.copilot import GiskardCopilotClient, ToolChatMessage
            from ...llm.talk.config import (
                ERROR_RESPONSE,
                MODEL_INSTRUCTION,
                SUMMARY_PROMPT,
                TALK_CLIENT_CONFIG,
            )
            from ..talk_result import TalkResult
        except ImportError as err:
            raise GiskardInstallationError(flavor="talk") from err

        client = GiskardCopilotClient()

        available_tools = self._get_available_tools(dataset, scan_report)

        system_prompt = MODEL_INSTRUCTION.format(
            tools_description="\n".join([tool.description for tool in list(available_tools.values())]),
            model_name=self.meta.name,
            model_description=self.meta.description,
            feature_names=self.meta.feature_names,
            context=context,
        )

        messages = [
            ToolChatMessage(role="system", content=system_prompt),
            ToolChatMessage(role="user", content=question),
        ]
        response = client.complete(
            messages=messages,
            tools=[tool.specification for tool in list(available_tools.values())],
            tool_choice="auto",
            **TALK_CLIENT_CONFIG,
        )

        if hasattr(response, "content") and response.content:
            messages.append(ToolChatMessage(role="assistant", content=response.content))

        # Store exceptions raised by tool execution.
        tool_errors = list()

        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = response.tool_calls
            response.tool_calls = [json.loads(tool_call.json()) for tool_call in tool_calls]
            messages.append(response)

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Get the reference to the chosen callable tool.
                tool = available_tools[tool_name]

                try:
                    tool_response = tool(**tool_args)
                except Exception as error_msg:
                    tool_response = ERROR_RESPONSE.format(
                        tool_name=tool_name, tool_args=tool_args, error_msg=error_msg.args[:1]
                    )
                    tool_errors.append(error_msg)

                # Append the tool's response to the conversation.
                messages.append(
                    ToolChatMessage(role="tool", name=tool_name, tool_call_id=tool_call.id, content=tool_response)
                )

            # Get the final model's response, based on the tool's output.
            response = client.complete(messages=messages, **TALK_CLIENT_CONFIG)
            messages.append(ToolChatMessage(role="assistant", content=response.content))

        # Summarise the conversation.
        context = self._gather_context(messages)
        summary = client.complete(
            messages=[ToolChatMessage(role="user", content=SUMMARY_PROMPT.format(context=context))],
            **TALK_CLIENT_CONFIG,
        )
        return TalkResult(response, summary, tool_errors)
