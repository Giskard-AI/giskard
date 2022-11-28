import json
from typing import Callable, Dict, Iterable, List, Optional, Union

import cloudpickle
import numpy as np
import pandas as pd
import requests
from pandas.api.types import is_numeric_dtype
from pandas.api.types import is_string_dtype
from requests_toolbelt.sessions import BaseUrlSession

from giskard.client.analytics_collector import GiskardAnalyticsCollector, anonymize
from giskard.client.io_utils import compress, pickle_dumps, save_df
from giskard.client.model import SupportedColumnType, SupportedModelTypes
from giskard.client.python_utils import get_python_requirements, get_python_version, warning


class GiskardProject:
    def __init__(
            self, session: BaseUrlSession, project_key: str, project_id: int,
            analytics: GiskardAnalyticsCollector = None
    ) -> None:
        self.project_key = project_key
        self._session = session
        self.url = self._session.base_url.replace("/api/v2/", "")
        self.analytics = analytics or GiskardAnalyticsCollector()
        self.project_id = project_id

    @staticmethod
    def _serialize(
            prediction_function: Callable[
                [pd.DataFrame],
                Iterable[Union[str, float, int]],
            ]
    ) -> bytes:
        compressed_pickle: bytes = compress(pickle_dumps(prediction_function))
        return compressed_pickle

    def upload_model(
            self,
            prediction_function: Callable[[pd.DataFrame], Iterable[Union[str, float, int]]],
            model_type: str,
            feature_names: List[str] = None,
            name: str = None,
            validate_df: pd.DataFrame = None,
            target: Optional[List[str]] = None,
            classification_threshold: Optional[float] = None,
            classification_labels: Optional[List[str]] = None,
    ):
        """
        Function to upload the Model to Giskard
        Args:
            prediction_function:
                The model you want to predict. It could be any Python function with the signature of
                predict_proba for classification: It returns the classification probabilities for all
                the classification labels
                predict for regression : It returns the predicted values for regression models.
            model_type:
                "classification" for classification model
                "regression" for regression model
            feature_names:
                 A list of the feature names of prediction_function. If provided, this list will be used to filter
                 the dataframe's columns before applying the model. By default, the dataframe is used as-is, meaning
                 that all of its columns are passed to the model.
                 Some important remarks:
                    - Make sure these features are contained in df
                    - Make sure that prediction_function(df[feature_names]) does not return an error message
                    - Make sure these features have the same order as the ones used in the
                      pipeline of prediction_function.
            name:
                The name of the model you want to upload
            validate_df:
                Dataset used to validate the model
            target:
                The column name in validate_df corresponding to the actual target variable (ground truth).
            classification_threshold:
                The probability threshold in the case of a binary classification model
            classification_labels:
                The classification labels of your prediction when prediction_task="classification".
                 Some important remarks:
                    - If classification_labels is a list of n elements, make sure prediction_function is
                     also returning probabilities
                    - Make sure the labels have the same order as the output of prediction_function
                    - Prefer using categorical values instead of numeric values in classification_labels
        """
        classification_labels, model = self._validate_model(
            classification_labels,
            classification_threshold,
            feature_names,
            model_type,
            prediction_function,
            target,
            validate_df,
        )
        return self._post_model(
            classification_labels, classification_threshold, feature_names, model, model_type, name
        )

    def _update_test_suite_params(self, actual_ds_id, reference_ds_id, model_id, test_id=None, test_suite_id=None):
        assert test_id is not None or test_suite_id is not None, "Either test_id or test_suite_id should be specified"
        res = self._session.put("testing/suites/update_params", json={
            "testSuiteId": test_suite_id,
            "testId": test_id,
            "referenceDatasetId": reference_ds_id,
            "actualDatasetId": actual_ds_id,
            "modelId": model_id
        })
        assert res.status_code == 200, "Failed to update test suite"

    def list_tests_in_suite(self, suite_id):
        assert suite_id is not None, "suite_id should be specified"
        res = self._session.get("testing/tests", params={"suiteId": suite_id}).json()
        return [{"id": t["id"], "name": t["name"]} for t in res]

    def list_test_suites(self):
        res = self._session.get(f"testing/suites/{self.project_id}").json()
        return [{"id": t["id"], "name": t["name"]} for t in res]

    def _execution_dto_filter(self, answer_json):
        res = {
            "id": answer_json['testId'],
            "name": answer_json['testName'],
            "status": answer_json['status'],

            "executionDate": answer_json['executionDate'],
            "message": answer_json['message']
        }
        if answer_json['status'] != 'ERROR':
            res["metric"] = answer_json['result'][0]['result']['metric']
        return res

    def execute_test(self, test_id, actual_ds_id=None, reference_ds_id=None, model_id=None):
        self.analytics.track(
            "execute_test",
            {
                "test_id": anonymize(test_id),
                "actual_ds_id": anonymize(actual_ds_id),
                "reference_ds_id": anonymize(reference_ds_id),
                "model_id": anonymize(model_id),
            },
        )
        assert test_id is not None, "test_id should be specified"

        self._update_test_suite_params(
            actual_ds_id, reference_ds_id, model_id, test_id=test_id
        )
        answer_json = self._session.post(f"testing/tests/{test_id}/run").json()
        return self._execution_dto_filter(answer_json)


    def execute_test_suite(self, test_suite_id, actual_ds_id=None, reference_ds_id=None, model_id=None):
        self.analytics.track(
            "execute_test_suite",
            {
                "test_suite_id": anonymize(test_suite_id),
                "actual_ds_id": anonymize(actual_ds_id),
                "reference_ds_id": anonymize(reference_ds_id),
                "model_id": anonymize(model_id),
            },
        )
        assert test_suite_id is not None, "test_suite_id should be specified"
        self._update_test_suite_params(
            actual_ds_id, reference_ds_id, model_id, test_suite_id=test_suite_id,
        )
        answer_json =  self._session.post(f"testing/suites/execute", json={"suiteId": test_suite_id}).json()
        return [self._execution_dto_filter(test) for test in answer_json]

    def _post_model(
            self,
            classification_labels,
            classification_threshold,
            feature_names,
            model,
            model_type,
            name,
    ):
        requirements = get_python_requirements()
        params = {
            "name": name,
            "projectKey": self.project_key,
            "languageVersion": get_python_version(),
            "modelType": model_type,
            "threshold": classification_threshold,
            "featureNames": feature_names,
            "language": "PYTHON",
            "classificationLabels": classification_labels,
        }
        files = [
            ("metadata", (None, json.dumps(params), "application/json")),
            ("modelFile", model),
            ("requirementsFile", requirements),
        ]
        model_res = self._session.post("project/models/upload", data={}, files=files)
        self.analytics.track(
            "Upload Model",
            {
                "name": anonymize(name),
                "projectKey": anonymize(self.project_key),
                "languageVersion": get_python_version(),
                "modelType": model_type,
                "threshold": classification_threshold,
                "featureNames": anonymize(feature_names),
                "language": "PYTHON",
                "classificationLabels": anonymize(classification_labels),
            },
        )

        model_id = model_res.json().get('id')
        print(
            f"Model successfully uploaded to project key '{self.project_key}' with ID = {model_id}. It is available at {self.url} "
        )
        return model_id

    def _validate_model(
            self,
            classification_labels,
            classification_threshold,
            feature_names,
            model_type,
            prediction_function,
            target,
            validate_df,
    ):
        prediction_function = self._validate_model_is_pickleable(prediction_function)
        transformed_pred_func = self.transform_prediction_function(
            prediction_function, feature_names
        )

        self._validate_prediction_function(prediction_function)
        self._validate_model_type(model_type)
        classification_labels = self._validate_classification_labels(
            classification_labels, model_type
        )

        if model_type == SupportedModelTypes.CLASSIFICATION.value:
            self._validate_classification_threshold_label(
                classification_labels, classification_threshold
            )

        assert feature_names is None or isinstance(
            feature_names, list
        ), "Invalid feature_names parameter. Please provide the feature names as a list."

        if validate_df is not None:
            self._validate_is_pandasdataframe(validate_df)
            self._validate_features(feature_names=feature_names, validate_df=validate_df)

            if model_type == SupportedModelTypes.REGRESSION.value:
                self._validate_model_execution(
                    transformed_pred_func, validate_df, model_type, target=target
                )
            elif target is not None and model_type == SupportedModelTypes.CLASSIFICATION.value:
                self._validate_target(target, validate_df.keys())
                target_values = validate_df[target].unique()
                self._validate_label_with_target(classification_labels, target_values, target)
                self._validate_model_execution(
                    transformed_pred_func,
                    validate_df,
                    model_type,
                    classification_labels,
                    target=target,
                )
            else:  # Classification with target = None
                self._validate_model_execution(
                    transformed_pred_func,
                    validate_df,
                    model_type,
                    classification_labels,
                    target=target,
                )

        model = self._serialize(transformed_pred_func)
        return classification_labels, model

    def upload_df(
            self,
            df: pd.DataFrame,
            column_types: Dict[str, str],
            target: str = None,
            name: str = None,
    ) -> requests.Response:
        """
        Function to upload Dataset to Giskard
        Args:
            df:
                Dataset you want to upload
            column_types:
                A dictionary of column names and their types (numeric, category or text) for all columns of df.
            target:
                The column name in df corresponding to the actual target variable (ground truth).
            name:
                The name of the dataset you want to upload
        Returns:
                Response of the upload
        """
        data, raw_column_types = self._validate_and_compress_data(column_types, df, target)
        result = self._post_data(column_types, data, name, raw_column_types, target)
        return result

    def _post_data(self, column_types, data, name, raw_column_types, target):
        params = {
            "projectKey": self.project_key,
            "name": name,
            "featureTypes": column_types,
            "columnTypes": raw_column_types,
            "target": target,
        }
        files = [("metadata", (None, json.dumps(params), "application/json")), ("file", data)]
        result = self._session.post("project/data/upload", data={}, files=files)
        ds_id = result.json().get('id')
        print(
            f"Dataset successfully uploaded to project key '{self.project_key}' with ID = {ds_id}. It is available at {self.url} "
        )
        self.analytics.track(
            "Upload dataset",
            {
                "projectKey": anonymize(self.project_key),
                "name": anonymize(name),
                "featureTypes": anonymize(column_types),
                "target": anonymize(target),
            },
        )
        return ds_id

    def _validate_and_compress_data(self, column_types, df, target):
        self._validate_is_pandasdataframe(df)
        if target is not None:
            self._validate_target(target, df.keys())
        self.validate_columns_columntypes(df, column_types, target)
        self._validate_column_types(column_types)
        self._validate_column_categorization(df, column_types)
        raw_column_types = df.dtypes.apply(lambda x: x.name).to_dict()
        data = compress(save_df(df))
        return data, raw_column_types

    def upload_model_and_df(
            self,
            prediction_function: Callable[[pd.DataFrame], Iterable[Union[str, float, int]]],
            model_type: str,
            df: pd.DataFrame,
            column_types: Dict[str, str],
            feature_names: List[str] = None,
            target: str = None,
            model_name: str = None,
            dataset_name: str = None,
            classification_threshold: Optional[float] = None,
            classification_labels: Optional[List[str]] = None,
    ):
        """
        Function to upload Dataset and model to Giskard
        Args:
            prediction_function:
                The model you want to predict. It could be any Python function with the signature of
                predict_proba for classification: It returns the classification probabilities for all
                the classification labels
                predict for regression : It returns the predicted values for regression models.
            model_type:
                "classification" for classification model
                "regression" for regression model
            df:
                Dataset you want to upload
            column_types:
                A dictionary of column names and their types (numeric, category or text) for all columns of df.
            feature_names:
                 A list of the feature names of prediction_function. If provided, this list will be used to filter
                 the dataframe's columns before applying the model. By default, the dataframe is used as-is, meaning
                 that all of its columns are passed to the model.
                 Some important remarks:
                    - Make sure these features are contained in df
                    - Make sure that prediction_function(df[feature_names]) does not return an error message
                    - Make sure these features have the same order as the ones used
                      in the pipeline of prediction_function.
            target:
                The column name in df corresponding to the actual target variable (ground truth).
            model_name:
                The name of the model you want to upload
            dataset_name:
                The name of the dataset you want to upload
            classification_threshold:
                The probability threshold in the case of a binary classification model
            classification_labels:
                The classification labels of your prediction when prediction_task="classification".
                 Some important remarks:
                    - If classification_labels is a list of n elements, make sure prediction_function is
                     also returning probabilities
                    - Make sure the labels have the same order as the output of prediction_function
                    - Prefer using categorical values instead of numeric values in classification_labels
        """
        self.analytics.track("Upload model and dataset")
        data, raw_column_types = self._validate_and_compress_data(column_types, df, target)
        classification_labels, model = self._validate_model(
            classification_labels,
            classification_threshold,
            feature_names,
            model_type,
            prediction_function,
            target,
            df,
        )
        data_res = self._post_data(column_types, data, dataset_name, raw_column_types, target)
        model_res = self._post_model(
            classification_labels,
            classification_threshold,
            feature_names,
            model,
            model_type,
            model_name,
        )
        return model_res, data_res

    @staticmethod
    def _validate_model_type(model_type):
        if model_type not in {task.value for task in SupportedModelTypes}:
            raise ValueError(
                f"Invalid model_type parameter: {model_type}. "
                + f"Please choose one of {[task.value for task in SupportedModelTypes]}."
            )

    @staticmethod
    def _validate_column_types(column_types):
        if column_types and isinstance(column_types, dict):
            if not set(column_types.values()).issubset(
                    set(column_type.value for column_type in SupportedColumnType)
            ):
                raise ValueError(
                    f"Invalid column_types parameter: "
                    + f"Please choose types among {[column_type.value for column_type in SupportedColumnType]}."
                )
        else:
            raise ValueError(
                f"Invalid column_types parameter: {column_types}. Please specify non-empty dictionary."
            )

    @staticmethod
    def transform_prediction_function(prediction_function, feature_names=None):
        if feature_names:
            return lambda df: prediction_function(df[feature_names])
        else:
            return prediction_function

    @staticmethod
    def _validate_prediction_function(prediction_function):
        if not callable(prediction_function):
            raise ValueError(
                f"Invalid prediction_function parameter: {prediction_function}. Please specify Python function."
            )

    @staticmethod
    def _validate_target(target, dataframe_keys):
        if target not in dataframe_keys:
            raise ValueError(
                f"Invalid target parameter:"
                f" {target} column is not present in the dataset with columns: {dataframe_keys}"
            )

    @staticmethod
    def _validate_features(feature_names=None, validate_df=None):
        if (
                feature_names is not None
                and validate_df is not None
                and not set(feature_names).issubset(set(validate_df.columns))
        ):
            missing_feature_names = set(feature_names) - set(validate_df.columns)
            raise ValueError(
                f"Value mentioned in  feature_names is  not available in validate_df: {missing_feature_names} "
            )

    @staticmethod
    def _validate_classification_threshold_label(
            classification_labels, classification_threshold=None
    ):
        if classification_labels is None:
            raise ValueError(f"Missing classification_labels parameter for classification model.")
        if classification_threshold is not None and not isinstance(
                classification_threshold, (int, float)
        ):
            raise ValueError(
                f"Invalid classification_threshold parameter: {classification_threshold}. Please specify valid number."
            )

        if classification_threshold is not None:
            if classification_threshold != 0.5:
                if len(classification_labels) != 2:
                    raise ValueError(
                        f"Invalid classification_threshold parameter: {classification_threshold} value is applicable "
                        f"only for binary classification. "
                    )

    @staticmethod
    def _validate_label_with_target(classification_labels, target_values=None, target_name=None):
        if target_values is not None:
            if not is_string_dtype(target_values):
                print(
                    'Hint: "Your target variable values are numeric. '
                    "It is recommended to have Human readable string as your target values "
                    'to make results more understandable in Giskard."'
                )

            target_values = (
                target_values
                if is_string_dtype(target_values)
                else [str(label) for label in target_values]
            )
            if not set(target_values).issubset(set(classification_labels)):
                invalid_target_values = set(target_values) - set(classification_labels)
                raise ValueError(
                    f"Values in {target_name} column are not declared in "
                    f"classification_labels parameter: {invalid_target_values}"
                )

    @staticmethod
    def _validate_classification_labels(classification_labels, model_type):
        res = None
        if model_type == SupportedModelTypes.CLASSIFICATION.value:
            if classification_labels is not None and isinstance(classification_labels, Iterable):  # type: ignore
                if len(classification_labels) > 1:
                    res: Optional[List[str]] = [str(label) for label in classification_labels]
                else:
                    raise ValueError(
                        f"Invalid classification_labels parameter: {classification_labels}. "
                        f"Please specify more than 1 label."
                    )
            else:
                raise ValueError(
                    f"Invalid classification_labels parameter: {classification_labels}. "
                    f"Please specify valid list of strings."
                )
        if model_type == SupportedModelTypes.REGRESSION.value and classification_labels is not None:
            warning("'classification_labels' parameter is ignored for regression model")
            res = None
        return res

    def _validate_model_execution(self, prediction_function, df: pd.DataFrame, model_type,
                                  classification_labels=None, target=None) -> None:
        if target is not None and target in df.columns:
            df = df.drop(target, axis=1)
        try:
            prediction_function(df.head(1))
        except Exception:
            raise ValueError("Invalid prediction_function input.\n"
                             "Please make sure that prediction_function(df.head(1)) does not return an error "
                             "message before uploading in Giskard")
        try:
            prediction = prediction_function(df)
        except Exception:
            raise ValueError(
                "Invalid prediction_function input.\n"
                "Please make sure that prediction_function(df[feature_names]) does not return an error "
                "message before uploading in Giskard"
            )
        min_num_rows = min(len(df), 5)
        GiskardProject._validate_deterministic_model(df.head(min_num_rows),
                                                     prediction[:min_num_rows],
                                                     prediction_function)
        GiskardProject._validate_prediction_output(df, model_type, prediction)
        if model_type == SupportedModelTypes.CLASSIFICATION.value:
            GiskardProject._validate_classification_prediction(classification_labels, prediction)

    @staticmethod
    def _validate_prediction_output(df: pd.DataFrame, model_type, prediction):
        assert len(df) == len(prediction), (
            f"Number of rows ({len(df)}) of dataset provided does not match with the "
            f"number of rows ({len(prediction)}) of prediction_function output"
        )
        if isinstance(prediction, np.ndarray) or isinstance(prediction, list):
            if model_type == SupportedModelTypes.CLASSIFICATION.value:
                if not any(isinstance(y, (np.floating, float)) for x in prediction for y in x):
                    raise ValueError("Model prediction should return float values ")
            if model_type == SupportedModelTypes.REGRESSION.value:
                if not any(isinstance(x, (np.floating, float)) for x in prediction):
                    raise ValueError("Model prediction should return float values ")
        else:
            raise ValueError("Model should return numpy array or a list")

    @staticmethod
    def _validate_classification_prediction(classification_labels, prediction):
        if not np.all(np.logical_and(prediction >= 0, prediction <= 1)):
            warning("Output of the prediction_function returns values out of range [0,1]. "
                    "The output of Multiclass and Binary classifications should be within the range [0,1]")
        if not np.all(np.isclose(np.sum(prediction, axis=1), 1, atol=0.0000001)):
            warning("Sum of output values of prediction_function is not equal to 1."
                    " For Multiclass and Binary classifications, the sum of probabilities should be 1")
        if prediction.shape[1] != len(classification_labels):
            raise ValueError(
                "Prediction output label shape and classification_labels shape do not match"
            )

    @staticmethod
    def validate_columns_columntypes(df: pd.DataFrame, feature_types, target) -> pd.DataFrame:
        columns_with_types = set(feature_types.keys())

        if target in df.columns:
            df = df.drop(target, axis=1)

        df_columns = set(df.columns)
        columns_with_types.discard(target)

        if not columns_with_types.issubset(df_columns):
            missing_columns = columns_with_types - df_columns
            raise ValueError(
                f"Missing columns in dataframe according to column_types: {missing_columns}"
            )
        elif not df_columns.issubset(columns_with_types):
            missing_columns = df_columns - columns_with_types
            if missing_columns:
                raise ValueError(
                    f"Invalid column_types parameter: Please declare the type for "
                    f"{missing_columns} columns"
                )

        pandas_inferred_column_types = df.dtypes.to_dict()
        for column, dtype in pandas_inferred_column_types.items():
            if (
                    feature_types.get(column) == SupportedColumnType.NUMERIC.value
                    and dtype == "object"
            ):
                try:
                    df[column] = df[column].astype(float)
                except Exception as e:
                    raise ValueError(f"Failed to convert column '{column}' to float") from e
            return df

    @staticmethod
    def _validate_column_categorization(df: pd.DataFrame, feature_types):
        nuniques = df.nunique()
        nuniques_category = 2
        nuniques_numeric = 100
        nuniques_text = 1000

        for column in df.columns:
            if nuniques[column] <= nuniques_category and \
                    (feature_types[column] == SupportedColumnType.NUMERIC.value or \
                     feature_types[column] == SupportedColumnType.TEXT.value):
                warning(
                    f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} (<= nuniques_category={nuniques_category}) distinct values. Are "
                    f"you sure it is not a 'category' feature?"
                )
            elif nuniques[column] > nuniques_text and is_string_dtype(df[column]) and \
                    (feature_types[column] == SupportedColumnType.CATEGORY.value or \
                     feature_types[column] == SupportedColumnType.NUMERIC.value):
                warning(
                    f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} (> nuniques_text={nuniques_text}) distinct values. Are "
                    f"you sure it is not a 'text' feature?"
                )
            elif nuniques[column] > nuniques_numeric and is_numeric_dtype(df[column]) and \
                    (feature_types[column] == SupportedColumnType.CATEGORY.value or \
                     feature_types[column] == SupportedColumnType.TEXT.value):
                warning(
                    f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} (> nuniques_numeric={nuniques_numeric}) distinct values. Are "
                    f"you sure it is not a 'numeric' feature?"
                )

    @staticmethod
    def _validate_is_pandasdataframe(df):
        assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"

    @staticmethod
    def _validate_deterministic_model(sample_df, prev_prediction, prediction_function):
        """
        Asserts if the model is deterministic by asserting previous and current prediction on same data
        """
        new_prediction = prediction_function(sample_df)

        if not np.allclose(prev_prediction, new_prediction):
            warning("Model is stochastic and not deterministic. Prediction function returns different results"
                    "after being invoked for the same data multiple times.")

    @staticmethod
    def _validate_model_is_pickleable(prediction_function):
        """
        Validates if the model can be pickled and un-pickled using cloud pickle
        """
        try:
            pickled_model = cloudpickle.dumps(prediction_function)
            unpickled_model = cloudpickle.loads(pickled_model)
        except Exception:
            raise ValueError("Unable to pickle or unpickle model on Giskard")
        return unpickled_model

    def __repr__(self) -> str:
        return f"GiskardProject(project_key='{self.project_key}')"
