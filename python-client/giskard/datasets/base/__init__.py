import inspect
import logging
import posixpath
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Optional, List, Union

import numpy as np
import pandas as pd
import yaml
from pandas.api.types import is_list_like
from zstandard import ZstdDecompressor

from giskard.client.giskard_client import GiskardClient
from giskard.client.io_utils import save_df, compress
from giskard.core.core import DatasetMeta, SupportedColumnTypes
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction, SlicingFunctionType
from giskard.ml_worker.testing.registry.transformation_function import (
    TransformationFunction,
    TransformationFunctionType,
)
from giskard.settings import settings
from giskard.client.python_utils import warning
from ..metadata.indexing import ColumnMetadataMixin

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    A class for processing tabular data using a pipeline of functions.

    The pipeline consists of slicing functions that extract subsets of the data and transformation functions that modify it.
    Slicing functions should take a pandas DataFrame as input and return a DataFrame, while transformation functions
    should take a DataFrame and return a modified version of it.

    Attributes:
        pipeline (List[Union[SlicingFunction, TransformationFunction]]): a list of functions to be applied to the data,
            in the order in which they were added.

    Methods:
        add_step(processor: Union[SlicingFunction, TransformationFunction]) -> DataProcessor:
            Add a function to the processing pipeline, if it is not already the last step in the pipeline. Return self.

        apply(dataset: Dataset, apply_only_last=False) -> Dataset:
            Apply the processing pipeline to the given dataset. If apply_only_last is True, apply only the last function
            in the pipeline. Return a new Dataset object containing the processed data.

        __repr__() -> str:
            Return a string representation of the DataProcessor object, showing the number of steps in its pipeline.
    """

    pipeline: List[Union[SlicingFunction, TransformationFunction]]

    def __init__(self):
        self.pipeline = []

    @configured_validate_arguments
    def add_step(self, processor: Union[SlicingFunction, TransformationFunction]):
        if not len(self.pipeline) or self.pipeline[-1] != processor:
            self.pipeline.append(processor)
        return self

    def apply(self, dataset: "Dataset", apply_only_last=False):
        ds = dataset.copy()

        while len(self.pipeline):
            step = self.pipeline.pop(-1 if apply_only_last else 0)

            df = step.execute(ds) if getattr(step, "needs_dataset", False) else step.execute(ds.df)
            ds = Dataset(
                df=df,
                name=ds.name,
                target=ds.target,
                cat_columns=ds.cat_columns,
                column_types=ds.column_types,
                validation=False,
            )

            if apply_only_last:
                break

        if len(self.pipeline):
            ds.data_processor = self

        return ds

    def __repr__(self) -> str:
        return f"<DataProcessor ({len(self.pipeline)} steps)>"


class Dataset(ColumnMetadataMixin):
    """
    A class for constructing and processing datasets.

    Attributes:
        dataset (pandas.DataFrame):
            A Pandas dataframe that contains some data examples that might interest you to inspect (test set, train set,
            production data). Some important remarks:

            - df should be the raw data that comes before all the preprocessing steps
            - df can contain more columns than the features of the model such as the actual ground truth variable,
            sample_id, metadata, etc.
        name (Optional[str]):
            A string representing the name of the dataset (default None).
        target (Optional[str]):
            The column name in df corresponding to the actual target variable (ground truth).
        cat_columns (Optional[List[str]]):
            A list of strings representing the names of categorical columns (default None). If not provided,
            the categorical columns will be automatically inferred.
        column_types (Optional[Dict[str, str]]):
            A dictionary of column names and their types (numeric, category or text) for all columns of df. If not provided,
            the categorical columns will be automatically inferred.
        data_processor (DataProcessor):
            An instance of the `DataProcessor` class used for data processing.
    """

    name: Optional[str]
    target: Optional[str]
    column_types: Dict[str, str]
    df: pd.DataFrame
    id: uuid.UUID
    data_processor: DataProcessor

    @configured_validate_arguments
    def __init__(
        self,
        df: pd.DataFrame,
        name: Optional[str] = None,
        target: Optional[str] = None,
        cat_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, str]] = None,
        id: Optional[uuid.UUID] = None,
        validation=True,
    ) -> None:
        """
        Initializes a Dataset object.

        Args:
            df (pd.DataFrame): The input dataset as a pandas DataFrame.
            name (Optional[str]): The name of the dataset.
            target (Optional[str]): The column name in df corresponding to the actual target variable (ground truth).
            cat_columns (Optional[List[str]]): A list of column names that are categorical.
            column_types (Optional[Dict[str, str]]): A dictionary mapping column names to their types.
            id (Optional[uuid.UUID]): A UUID that uniquely identifies this dataset.

        Notes:
            if neither of cat_columns or column_types are provided. We infer heuristically the types of the columns.
            See the _infer_column_types method.
        """
        if id is None:
            self.id = uuid.uuid4()
        else:
            self.id = id
        self.name = name
        self.df = pd.DataFrame(df)
        self.target = target

        if validation:
            from giskard.core.dataset_validation import validate_dtypes, validate_target

            validate_dtypes(self)
            validate_target(self)

        self.column_dtypes = self.extract_column_dtypes(self.df)

        # used in the inference of category columns
        self.category_threshold = round(np.log10(len(self.df))) if len(self.df) >= 100 else 2
        self.column_types = self._infer_column_types(column_types, cat_columns)
        if validation:
            from giskard.core.dataset_validation import validate_column_types

            validate_column_types(self)

        if validation:
            from giskard.core.dataset_validation import validate_column_categorization, validate_numeric_columns

            validate_column_categorization(self)
            validate_numeric_columns(self)

        logger.info("Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.")

        self.data_processor = DataProcessor()

    def add_slicing_function(self, slicing_function: SlicingFunction):
        """
        Adds a slicing function to the data processor.

        Args:
            slicing_function (SlicingFunction): A slicing function to add to the data processor.
        """
        self.data_processor.add_step(slicing_function)
        return self

    def add_transformation_function(self, transformation_function: TransformationFunction):
        """
        Add a transformation function to the data processor's list of steps.

        Args:
            transformation_function (TransformationFunction): A transformation function to add to the data processor.
        """
        self.data_processor.add_step(transformation_function)
        return self

    @configured_validate_arguments
    def slice(
        self,
        slicing_function: Union[SlicingFunction, SlicingFunctionType],
        row_level: bool = True,
        cell_level=False,
        column_name: Optional[str] = None,
    ):
        """
        Slice the dataset using the specified `slicing_function`.

        Args:
            slicing_function (Union[SlicingFunction, SlicingFunctionType]): A slicing function to apply.
                If `slicing_function` is a callable, it will be wrapped in a `SlicingFunction` object
                with `row_level` as its `row_level` argument. The `SlicingFunction` object will be
                used to slice the DataFrame. If `slicing_function` is a `SlicingFunction` object, it
                will be used directly to slice the DataFrame.
            row_level (bool): Whether the `slicing_function` should be applied to the rows (True) or
                the whole dataframe (False). Defaults to True.

        Returns:
            Dataset:
                The sliced dataset as a `Dataset` object.

        Notes:
            Raises TypeError: If `slicing_function` is not a callable or a `SlicingFunction` object.
        """
        if inspect.isfunction(slicing_function):
            slicing_function = SlicingFunction(slicing_function, row_level=row_level, cell_level=cell_level)

        if slicing_function.cell_level and column_name is not None:
            slicing_function = slicing_function(column_name=column_name, **slicing_function.params)

        return self.data_processor.add_step(slicing_function).apply(self, apply_only_last=True)

    @configured_validate_arguments
    def transform(
        self,
        transformation_function: Union[TransformationFunction, TransformationFunctionType],
        row_level: bool = True,
        cell_level=False,
        column_name: Optional[str] = None,
    ):
        """
        Transform the data in the current Dataset by applying a transformation function.

        Args:
            transformation_function (Union[TransformationFunction, TransformationFunctionType]):
                A transformation function to apply. If `transformation_function` is a callable, it will
                be wrapped in a `TransformationFunction` object with `row_level` as its `row_level`
                argument. If `transformation_function` is a `TransformationFunction` object, it will be used
                directly to transform the DataFrame.
            row_level (bool): Whether the `transformation_function` should be applied to the rows (True) or
                the whole dataframe (False). Defaults to True.

        Returns:
            Dataset: A new Dataset object containing the transformed data.

        Notes:
            Raises TypeError: If `transformation_function` is not a callable or a `TransformationFunction` object.
        """

        if inspect.isfunction(transformation_function):
            transformation_function = TransformationFunction(
                transformation_function, row_level=row_level, cell_level=cell_level
            )

        if transformation_function.cell_level and column_name is not None:
            transformation_function = transformation_function(column_name=column_name, **transformation_function.params)

        assert (
            not transformation_function.cell_level or 'column_name' in transformation_function.params
        ), "column_name should be provided for TransformationFunction at cell level"
        return self.data_processor.add_step(transformation_function).apply(self, apply_only_last=True)

    def process(self):
        """
        Process the dataset by applying all the transformation and slicing functions in the defined order.

        Returns:
            The processed dataset after applying all the transformation and slicing functions.
        """
        return self.data_processor.apply(self)

    def _infer_column_types(self, column_types: Optional[Dict[str, str]], cat_columns: Optional[List[str]]):
        """
        Infer column types of a given DataFrame based on the number of unique values and column data types.

        Args:
            df (pandas.DataFrame): The DataFrame to infer column types for.
            column_dtypes (dict): A dictionary that maps column names to their expected data types.
            no_cat (bool, optional): If True, do not infer categories and treat them as text instead.

        Returns:
            dict: A dictionary that maps column names to their inferred types, one of 'text', 'numeric', or 'category'.
        """
        if not column_types:
            column_types = {}
        df_columns = set(self.df.columns.drop(self.target)) if self.target else set(self.df.columns)

        # priority of cat_columns over column_types (for categorical columns)
        if cat_columns:
            if not set(cat_columns).issubset(df_columns):
                raise ValueError(
                    "The provided 'cat_columns' are not all part of your dataset 'columns'. "
                    "Please make sure that `cat_columns` refers to existing columns in your dataset."
                )
            for cat_col in cat_columns:
                if cat_col != self.target:
                    column_types[cat_col] = SupportedColumnTypes.CATEGORY.value

        given_columns = set(column_types.keys())
        unknown_columns = given_columns - df_columns
        missing_columns = df_columns - given_columns

        if unknown_columns:
            warning(
                f"The provided keys {list(unknown_columns)} in 'column_types' are not part of your dataset "
                "'columns'. Please make sure that the column names in `column_types` refers to existing "
                "columns in your dataset."
            )
            [column_types.pop(i) for i in unknown_columns]

        if not missing_columns:
            column_types.pop(self.target, None)  # no need for target type
            return column_types

        nuniques = self.df.nunique()
        for col in missing_columns:
            if col == self.target:
                continue
            if nuniques[col] <= self.category_threshold:
                column_types[col] = SupportedColumnTypes.CATEGORY.value
                continue
            # inference of text and numeric columns
            try:
                pd.to_numeric(self.df[col])
                column_types[col] = SupportedColumnTypes.NUMERIC.value
            except ValueError:
                column_types[col] = SupportedColumnTypes.TEXT.value

        return column_types

    @staticmethod
    def extract_column_dtypes(df):
        """
        Extracts the column data types from a pandas DataFrame.

        Args:
            df (pandas.DataFrame): The input DataFrame.

        Returns:
            dict: A dictionary where the keys are the column names and the values are the corresponding data types as strings.
        """
        return df.dtypes.apply(lambda x: x.name).to_dict()

    def upload(self, client: GiskardClient, project_key: str):
        """
        Uploads the dataset to the specified Giskard project.

        Args:
            client: A GiskardClient instance for connecting to the Giskard API.
            project_key (str): The key of the project to upload the dataset to.

        Returns:
            str: The ID of the uploaded dataset.
        """
        dataset_id = str(self.id)

        with tempfile.TemporaryDirectory(prefix="giskard-dataset-") as local_path:
            original_size_bytes, compressed_size_bytes = self.save(Path(local_path), dataset_id)
            client.log_artifacts(local_path, posixpath.join(project_key, "datasets", dataset_id))
            client.save_dataset_meta(
                project_key,
                dataset_id,
                self.meta,
                original_size_bytes=original_size_bytes,
                compressed_size_bytes=compressed_size_bytes,
            )
        return dataset_id

    @property
    def meta(self):
        return DatasetMeta(
            name=self.name, target=self.target, column_types=self.column_types, column_dtypes=self.column_dtypes
        )

    @staticmethod
    def cast_column_to_dtypes(df, column_dtypes):
        current_types = df.dtypes.apply(lambda x: x.name).to_dict()
        logger.info(f"Casting dataframe columns from {current_types} to {column_dtypes}")
        if column_dtypes:
            try:
                df = df.astype(column_dtypes)
            except Exception as e:
                raise ValueError("Failed to apply column types to dataset") from e
        return df

    @classmethod
    def load(cls, local_path: str):
        with open(local_path, "rb") as ds_stream:
            return pd.read_csv(
                ZstdDecompressor().stream_reader(ds_stream),
                keep_default_na=False,
                na_values=["_GSK_NA_"],
            )

    @classmethod
    def download(cls, client: GiskardClient, project_key, dataset_id):
        """
        Downloads a dataset from a Giskard project and returns a Dataset object.
        If the client is None, then the function assumes that it is running in an internal worker and looks for the dataset locally.

        Args:
            client (GiskardClient):
                The GiskardClient instance to use for downloading the dataset.
                If None, the function looks for the dataset locally.
            project_key (str): The key of the Giskard project that the dataset belongs to.
            dataset_id (str): The ID of the dataset to download.

        Returns:
            Dataset: A Dataset object that represents the downloaded dataset.
        """
        local_dir = settings.home_dir / settings.cache_dir / project_key / "datasets" / dataset_id

        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing dataset {project_key}.{dataset_id}"
            with open(Path(local_dir) / "giskard-dataset-meta.yaml") as f:
                saved_meta = yaml.load(f, Loader=yaml.Loader)
                meta = DatasetMeta(
                    name=saved_meta["name"],
                    target=saved_meta["target"],
                    column_types=saved_meta["column_types"],
                    column_dtypes=saved_meta["column_dtypes"],
                )
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "datasets", dataset_id))
            meta: DatasetMeta = client.load_dataset_meta(project_key, dataset_id)

        df = cls.load(local_dir / "data.csv.zst")
        df = cls.cast_column_to_dtypes(df, meta.column_dtypes)
        return cls(df=df, name=meta.name, target=meta.target, column_types=meta.column_types, id=uuid.UUID(dataset_id))

    @staticmethod
    def _cat_columns(meta):
        return (
            [fname for (fname, ftype) in meta.column_types.items() if ftype == SupportedColumnTypes.CATEGORY]
            if meta.column_types
            else None
        )

    @property
    def cat_columns(self):
        return self._cat_columns(self.meta)

    def save(self, local_path: Path, dataset_id):
        with open(local_path / "data.csv.zst", "wb") as f:
            uncompressed_bytes = save_df(self.df)
            compressed_bytes = compress(uncompressed_bytes)
            f.write(compressed_bytes)
            original_size_bytes, compressed_size_bytes = len(uncompressed_bytes), len(compressed_bytes)

            with open(Path(local_path) / "giskard-dataset-meta.yaml", "w") as meta_f:
                yaml.dump(
                    {
                        "id": dataset_id,
                        "name": self.meta.name,
                        "target": self.meta.target,
                        "column_types": self.meta.column_types,
                        "column_dtypes": self.meta.column_dtypes,
                        "original_size_bytes": original_size_bytes,
                        "compressed_size_bytes": compressed_size_bytes,
                    },
                    meta_f,
                    default_flow_style=False,
                )
            return original_size_bytes, compressed_size_bytes

    @property
    def columns(self):
        return self.df.columns

    def __len__(self):
        return len(self.df)

    def select_columns(self, columns=None, col_type=None):
        columns = _cast_to_list_like(columns) if columns is not None else None
        col_type = _cast_to_list_like(col_type) if col_type is not None else None

        df = self.df.copy()

        if columns is None and col_type is None:
            # TODO: should probably copy
            return self

        # Filter by columns
        if columns is not None:
            df = df.loc[:, columns]

        # Filter by type
        if col_type is not None:
            if not is_list_like(col_type):
                col_type = [col_type]

            columns = [col for col in df.columns if self.column_types[col] in col_type]
            df = df.loc[:, columns]

        return Dataset(
            df=df,
            target=self.target if self.target in df.columns else None,
            column_types={key: val for key, val in self.column_types.items() if key in df.columns},
            validation=False,
        )

    def copy(self):
        return Dataset(df=self.df.copy(), target=self.target, column_types=self.column_types.copy(), validation=False)


def _cast_to_list_like(object):
    return object if is_list_like(object) else (object,)
