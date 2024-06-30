from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Hashable, List, Optional, Union

import inspect
import logging
import tempfile
import uuid
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas
import pandas as pd
import yaml
from pandas.api.types import is_list_like, is_numeric_dtype
from xxhash import xxh3_128_hexdigest
from zstandard import ZstdDecompressor

from giskard.client.io_utils import compress, save_df
from giskard.client.python_utils import warning
from giskard.core.core import NOT_GIVEN, DatasetMeta, NotGivenOr, SupportedColumnTypes
from giskard.core.errors import GiskardImportError
from giskard.core.validation import configured_validate_arguments
from giskard.registry.slicing_function import SlicingFunction, SlicingFunctionType
from giskard.registry.transformation_function import (
    TransformationFunction,
    TransformationFunctionType,
)

from ...utils.analytics_collector import analytics
from ..metadata.indexing import ColumnMetadataMixin

if TYPE_CHECKING:
    from mlflow import MlflowClient

SAMPLE_SIZE = 1000

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

    def apply(self, dataset: "Dataset", apply_only_last=False, get_mask: bool = False, copy: bool = True):
        if copy:
            ds = dataset.copy()
        else:
            ds = dataset
        is_slicing_only = True

        while len(self.pipeline):
            step = self.pipeline.pop(-1 if apply_only_last else 0)
            is_slicing_only = is_slicing_only and isinstance(step, SlicingFunction)
            df = step.execute(ds) if getattr(step, "needs_dataset", False) else step.execute(ds.df)
            ds = Dataset(
                df=df,
                name=ds.name,
                target=ds.target,
                cat_columns=ds.cat_columns,
                column_types=ds.column_types,
                validation=False,
                original_id=dataset.original_id,
            )

            if apply_only_last:
                break

        if get_mask:
            return dataset.df.index.isin(df.index)  # returns a boolean numpy.ndarray of shape len(dataset.df)
        else:
            if len(self.pipeline):
                ds.data_processor = self

            # If dataset had metadata, copy it to the new dataset
            if is_slicing_only and hasattr(dataset, "column_meta"):
                ds.load_metadata_from_instance(dataset.column_meta)

            return ds

    def __repr__(self) -> str:
        return f"<DataProcessor ({len(self.pipeline)} steps)>"


class Dataset(ColumnMetadataMixin):
    """
    To scan, test and debug your model, you need to provide a dataset that can be executed by your model.
    This dataset can be your training, testing, golden, or production dataset.

    The ``pandas.DataFrame`` you provide should contain the **raw data before pre-processing** (categorical encoding, scaling,
    etc.). The prediction function that you wrap with the Giskard `Model` should be able to
    execute the pandas dataframe.


    Attributes:
        df (pandas.DataFrame):
            A `pandas.DataFrame` that contains the raw data (before all the pre-processing steps) and the actual
            ground truth variable (target). `df` can contain more columns than the features of the model, such as the sample_id,
            metadata, etc.
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
    """

    name: Optional[str]
    _target: NotGivenOr[Optional[str]]
    column_types: Dict[str, str]
    df: pd.DataFrame
    id: uuid.UUID
    original_id: uuid.UUID
    data_processor: DataProcessor

    @configured_validate_arguments
    def __init__(
        self,
        df: pd.DataFrame,
        name: Optional[str] = None,
        target: NotGivenOr[Optional[Hashable]] = NOT_GIVEN,
        cat_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[Hashable, str]] = None,
        id: Optional[uuid.UUID] = None,
        validation=True,
        original_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Initializes a Dataset object.

        Args:
            df (pd.DataFrame): The input dataset as a pandas DataFrame.
            name (Optional[str]): The name of the dataset.
            target (Optional[str]): The column name in df corresponding to the actual target variable (ground truth). The target needs to be explicitly set to `None` if the dataset doesn't have any target variable.
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
        self.original_id = original_id or self.id

        self.name = name
        self.df = pd.DataFrame(df)
        self._target = target

        if validation:
            from giskard.core.dataset_validation import validate_dataset

            validate_dataset(self)

        self.column_dtypes = self.extract_column_dtypes(self.df)

        # used in the inference of category columns
        df_size = len(self.df)
        # if df_size >= 100     ==> category_threshold = floor(log10(df_size))
        # if 2 < df_size < 100  ==> category_threshold = 2
        # if df_size <= 2       ==> category_threshold = 0 (column is text)
        # df_size != 0 to avoid <stdin>:1: RuntimeWarning: divide by zero encountered in log10
        self.category_threshold = max(np.floor(np.log10(df_size)), 2) * (df_size > 2) if df_size != 0 else 0
        self.column_types = self._infer_column_types(column_types, cat_columns, validation)
        if validation:
            from giskard.core.dataset_validation import validate_column_types

            validate_column_types(self)

        if validation:
            from giskard.core.dataset_validation import (
                validate_column_categorization,
                validate_numeric_columns,
            )

            validate_column_categorization(self)
            validate_numeric_columns(self)

        self.number_of_rows = len(self.df.index)
        self.category_features = {
            column: list(map(lambda x: str(x), self.df[column].dropna().unique()))
            for column, column_type in self.column_types.items()
            if column_type == "category"
        }

        self.data_processor = DataProcessor()
        if validation:
            logger.info("Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.")

    @property
    def is_target_given(self) -> bool:
        return self._target is not NOT_GIVEN

    @property
    def target(self) -> Optional[str]:
        return self._target or None

    def add_slicing_function(self, slicing_function: SlicingFunction):
        """
        Adds a slicing function to the data processor's list of steps.

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
    def filter(self, mask: List[int], axis: int = 0):
        """
        Filter the dataset using the specified `mask`.

        Args:
            mask (List[int]): A mask of int values to apply.
            axis (int): The axis on which the `mask` should be applied. axis = 0 by default.

        Returns:
            Dataset:
                The filtered dataset as a `Dataset` object.

        """
        return Dataset(
            df=self.df.filter(mask, axis=axis),
            name=self.name,
            target=self.target,
            cat_columns=self.cat_columns,
            column_types=self.column_types,
            validation=False,
        )

    @cached_property
    def row_hashes(self):
        return pandas.Series(
            map(
                lambda row: xxh3_128_hexdigest(f"{', '.join(map(lambda x: repr(x), row))}".encode("utf-8")),
                self.df.values,
            ),
            index=self.df.index,
        )

    @configured_validate_arguments
    def slice(
        self,
        slicing_function: Union[SlicingFunction, SlicingFunctionType],
        row_level: bool = True,
        get_mask: bool = False,
        cell_level=False,
        column_name: Optional[str] = None,
    ):
        """
        Slice the dataset using the specified `slicing_function`.

        Args:
            slicing_function (Union[SlicingFunction, SlicingFunctionType]): A slicing function to apply.
                If `slicing_function` is a callable, it will be wrapped in a `SlicingFunction` object
                with `row_level` and `cell_level` as its arguments. The `SlicingFunction` object will be
                used to slice the DataFrame. If `slicing_function` is a `SlicingFunction` object, it
                will be used directly to slice the DataFrame.
            row_level (bool): Whether the `slicing_function` should be applied to the rows (True) or
                the whole dataframe (False). Defaults to True.
            get_mask (bool): Whether the `slicing_function` returns a dataset (False) or a mask, i.e.
                a list of indices (True).
            cell_level (bool): Whether the `slicing_function` should be applied to the cells (True) or
                the whole dataframe (False). Defaults to False.

        Returns:
            Dataset:
                The sliced dataset as a `Dataset` object.

        Notes:
            Raises TypeError: If `slicing_function` is not a callable or a `SlicingFunction` object.
        """
        if inspect.isfunction(slicing_function):
            slicing_function = SlicingFunction(slicing_function, row_level=row_level, cell_level=cell_level)

        if slicing_function.cell_level and column_name is not None:
            slicing_function = slicing_function(
                column_name=column_name,
                **{key: value for key, value in slicing_function.params.items() if key != "column_name"},
            )

        return self.data_processor.add_step(slicing_function).apply(
            self, apply_only_last=True, get_mask=get_mask, copy=False
        )

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
                be wrapped in a `TransformationFunction` object with `row_level` and `cell_level` as its
                arguments. If `transformation_function` is a `TransformationFunction` object, it will be used
                directly to transform the DataFrame.
            row_level (bool): Whether the `transformation_function` should be applied to the rows (True) or
                the whole dataframe (False). Defaults to True.
            cell_level (bool): Whether the `slicing_function` should be applied to the cells (True) or
                the whole dataframe (False). Defaults to False.

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
            transformation_function = transformation_function(
                column_name=column_name,
                **{key: value for key, value in transformation_function.params.items() if key != "column_name"},
            )

        assert (
            not transformation_function.cell_level or "column_name" in transformation_function.params
        ), "column_name should be provided for TransformationFunction at cell level"
        return self.data_processor.add_step(transformation_function).apply(self, apply_only_last=True)

    def process(self):
        """
        Process the dataset by applying all the transformation and slicing functions in the defined order.

        Returns:
            The processed dataset after applying all the transformation and slicing functions.
        """
        return self.data_processor.apply(self)

    def _infer_column_types(
        self,
        column_types: Optional[Dict[str, str]],
        cat_columns: Optional[List[str]],
        validation: bool = True,
    ):
        """
        This function infers the column types of a given DataFrame based on the number of unique values and column data types. It takes into account the provided column types and categorical columns. The inferred types can be 'text', 'numeric', or 'category'. The function also applies a logarithmic rule to determine the category threshold.

        Here's a summary of the function's logic:

        1. If no column types are provided, initialize an empty dictionary.
        2. Determine the columns in the DataFrame, excluding the target column if it exists.
        3. If categorical columns are specified, prioritize them over the provided column types and mark them as 'category'.
        4. Check for any unknown columns in the provided column types and remove them from the dictionary.
        5. If there are no missing columns, remove the target column (if present) from the column types dictionary.
        6. Calculate the number of unique values in each missing column.
        7. For each missing column:

           - If the number of unique values is less than or equal to the category threshold, categorize it as 'category'.
           - Otherwise, attempt to convert the column to numeric using `pd.to_numeric` and categorize it as 'numeric'.
           - If the column does not have the expected numeric data type and validation is enabled, issue a warning message.
           - If conversion to numeric raises a ValueError, categorize the column as 'text'.
        8. Return the column types dictionary.

        The logarithmic rule is used to calculate the category threshold. The formula is: `category_threshold = round(np.log10(len(self.df))) if len(self.df) >= 100 else 2`. This means that if the length of the DataFrame is greater than or equal to 100, the category threshold is set to the rounded value of the base-10 logarithm of the DataFrame length. Otherwise, the category threshold is set to 2. The logarithmic rule helps in dynamically adjusting the category threshold based on the size of the DataFrame.

        Returns:
           dict: A dictionary that maps column names to their inferred types, one of 'text', 'numeric', or 'category'.
        """
        if not column_types:
            column_types = {}
        df_columns = set([col for col in self.columns if col != self.target]) if self.target else set(self.columns)

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
                if not is_numeric_dtype(self.df[col]) and validation:
                    warning(
                        f"The column {col} is declared as numeric but has '{str(self.df[col].dtype)}' as data type. "
                        "To avoid potential future issues, make sure to cast this column to the correct data type."
                    )

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

    def extract_languages(self, columns=None):
        """
        Extracts all languages present in the dataset 'text' column.

        Args:
            list[str]: a list of columns from which languages should be extracted.

        Returns:
            list[str]: a list of language codes (according to  ISO 639-1) containing all languages in the dataset.
        """
        columns = columns if columns is not None else self.columns

        langs_per_feature = [
            self.column_meta[col, "text"]["language"].dropna().unique()
            for col, col_type in self.column_types.items()
            if (col_type == "text" and col in columns)
        ]

        return list(set().union(*langs_per_feature))

    @property
    def meta(self):
        return DatasetMeta(
            name=self.name,
            target=self.target,
            column_types=self.column_types,
            column_dtypes=self.column_dtypes,
            number_of_rows=self.number_of_rows,
            category_features=self.category_features,
        )

    @staticmethod
    def cast_column_to_dtypes(df, column_dtypes):
        current_types = df.dtypes.apply(lambda x: x.name).to_dict()
        logger.info(f"Casting dataframe columns from {current_types} to {column_dtypes}")
        if column_dtypes:
            try:
                df = df.astype(column_dtypes, errors="ignore")
            except Exception as e:
                raise ValueError("Failed to apply column types to dataset") from e
        return df

    @classmethod
    def load(cls, local_path: str):
        with open(local_path, "rb") as ds_stream:
            return pd.read_csv(
                ZstdDecompressor().stream_reader(ds_stream), keep_default_na=False, na_values=["_GSK_NA_"]
            )

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
        with open(local_path / "data.csv.zst", "wb") as f, open(local_path / "data.sample.csv.zst", "wb") as f_sample:
            uncompressed_bytes = save_df(self.df)
            compressed_bytes = compress(uncompressed_bytes)
            f.write(compressed_bytes)
            original_size_bytes, compressed_size_bytes = len(uncompressed_bytes), len(compressed_bytes)

            uncompressed_bytes = save_df(self.df.sample(min(SAMPLE_SIZE, len(self.df.index))))
            compressed_bytes = compress(uncompressed_bytes)
            f_sample.write(compressed_bytes)

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
                        "number_of_rows": self.meta.number_of_rows,
                        "category_features": self.meta.category_features,
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
        dataset = Dataset(
            df=self.df.copy(),
            target=self.target,
            column_types=self.column_types.copy(),
            validation=False,
        )

        if hasattr(self, "column_meta"):
            dataset.load_metadata_from_instance(self.column_meta)

        return dataset

    def to_mlflow(self, mlflow_client: MlflowClient = None, mlflow_run_id: str = None):
        import mlflow

        # To avoid file being open in write mode and read at the same time,
        # First, we'll write it, then make sure to remove it
        with tempfile.NamedTemporaryFile(prefix="dataset-", suffix=".csv", delete=False) as f:
            # Get file path
            local_path = f.name
            # Get name from file
            artifact_name = Path(f.name).name
            # Write the file on disk
            f.write(save_df(self.df))
        try:
            if mlflow_client is None and mlflow_run_id is None:
                mlflow.log_artifact(local_path)
            elif mlflow_client and mlflow_run_id:
                mlflow_client.log_artifact(mlflow_run_id, local_path=local_path)
            else:
                raise ValueError(
                    f"Unhandled case, both clien and id should be defined, or none. mlflow_client:{mlflow_client} mlflow_run_id:{mlflow_run_id}"
                )
        finally:
            # Force deletion of the temps file
            Path(f.name).unlink(missing_ok=True)

        return artifact_name

    def to_wandb(self, run: Optional["wandb.wandb_sdk.wandb_run.Run"] = None) -> None:  # noqa
        """Log the dataset to the WandB run.

        Log the current dataset in a table format to the active WandB run.

        Parameters
        ----------
        run :
            WandB run.
        """
        try:
            import wandb  # noqa
        except ImportError as e:
            raise GiskardImportError("wandb") from e
        from ...integrations.wandb.wandb_utils import get_wandb_run

        run = get_wandb_run(run)

        run.log({"Dataset/dataset": wandb.Table(dataframe=self.df)})

        analytics.track(
            "wandb_integration:dataset",
            {
                "wandb_run_id": run.id,
                "dataset_size": len(self.df),
                "dataset_cat_col_cnt": len([c for c, t in self.column_types.items() if t == "category"]),
                "dataset_num_col_cnt": len([c for c, t in self.column_types.items() if t == "numeric"]),
                "dataset_text_col_cnt": len([c for c, t in self.column_types.items() if t == "text"]),
            },
        )

    def __str__(self) -> str:
        if self.name:  # handle both None and empty string
            return f"{self.name}({self.id})"
        return super().__str__()  # default to `<giskard.datasets.base.Dataset object at ...>`


def _cast_to_list_like(object):
    return object if is_list_like(object) else (object,)
