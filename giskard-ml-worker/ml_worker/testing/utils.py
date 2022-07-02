import os

from generated.ml_worker_pb2 import SingleTestResult
from zstandard import ZstdCompressor, ZstdDecompressor
from typing import Optional
from io import BytesIO
import re
import pandas as pd
import numpy as np

COMPRESSION_MAX_OUTPUT_SIZE = 10 ** 9  # 1GB


def ge_result_to_test_result(result, passed=True) -> SingleTestResult:
    """
        Converts a result of Great Expectations to TestResultMessage - java/python bridge test result class
    :param passed: boolean flag containing result of a test
    :param result: Great Expectations result
    :return: TestResultMessage - a protobuf generated test result class
    """

    return SingleTestResult(
        passed=passed,
        actual_slices_size=[result['element_count']],
        missing_count=result['missing_count'],
        missing_percent=result['missing_percent'],
        unexpected_count=result['unexpected_count'],
        unexpected_percent=result['unexpected_percent'],
        unexpected_percent_total=result['unexpected_percent_total'],
        unexpected_percent_nonmissing=result['unexpected_percent_nonmissing'],
        partial_unexpected_index_list=result['partial_unexpected_index_list'],
        unexpected_index_list=result['unexpected_index_list']
    )


def apply_perturbation_inplace(df, perturbation_dict):
    modified_rows = []
    i = 0
    for idx, r in df.iterrows():
        added = False
        for pert_col, pert_func in perturbation_dict.items():
            original_value = r[pert_col]
            new_value = pert_func(r)
            if original_value != new_value and not added:
                added = True
                modified_rows.append(i)
                df.loc[idx, pert_col] = new_value
        i += 1
    return modified_rows


def save_df(df: pd.DataFrame, format: str = "csv") -> bytes:
    pandas_version: int = int(re.sub("\D", "", pd.__version__))
    if format == "csv":
        csv_buffer = BytesIO()
        if pandas_version >= 120:
            df.to_csv(csv_buffer, index=False)
        else:
            csv_buffer.write(df.to_csv(index=False).encode("utf-8"))
            csv_buffer.seek(0)
        return csv_buffer.getvalue()
    else:
        raise ValueError("Invalid method: {method}. Choose 'csv'.")


def compress(data: bytes, method: Optional[str] = "zstd") -> bytes:
    if method == "zstd":
        compressor = ZstdCompressor(level=3, write_checksum=True)
        compressed_data = compressor.compress(data)
    elif method is None:
        compressed_data = data
    else:
        raise ValueError("Invalid compression method: {method}. Choose 'zstd' or None.")

    return compressed_data


def decompress(
        data: bytes, method: Optional[str] = "zstd", max_output_size: int = COMPRESSION_MAX_OUTPUT_SIZE
) -> bytes:
    if method == "zstd":
        decompressor = ZstdDecompressor()
        decompressed_data = decompressor.decompress(data, max_output_size=max_output_size)
    elif method is None:
        decompressed_data = data
    else:
        raise ValueError("Invalid compression method: {method}. Choose 'zstd' or None.")
    return decompressed_data


def bin_numerical_values(data_series, labels=None, bins=None):
    """
    Bin numerical values into quantile partitions to convert numerical value as categorical value to compute drifts
    """
    if labels is not None and bins is not None:
        # Convert actual dataset based on bins of reference dataset

        if data_series.min() <= bins[0]:
            # If actual dataset set has value smaller than the minimum bin of reference,
            # it is added in the bin with label -1
            print(f"Miniumum value {data_series.min()} of Actual Dataset has been appended in the bin")
            bins = np.insert(bins, 0, data_series.min())
            labels = np.insert(labels, 0, -1)

        if data_series.max() >= bins[-1]:
            # If actual dataset set has value larger than the maximum bin of reference,
            # it is added in the bin with label [last bin value + 1]
            print(f"Maximum value {data_series.max()} of Actual Dataset has been appended in the bin")
            bins = np.append(bins, data_series.max())
            labels = np.append(labels, (labels[-1] + 1))

        converted_series = pd.cut(data_series, bins=bins, labels=labels, include_lowest=True)
        labels = None
        bins = None
    else:
        # Convert reference dataset into 10 quantiles

        # User can define the bin length by declaring GSK_TEST_DRIFT_BIN_COUNT
        deciles_value = os.environ.get('GSK_TEST_DRIFT_BIN_COUNT', int(0.1 * len(data_series)))
        converted_tuple = pd.qcut(data_series, deciles_value, labels=range(deciles_value), retbins=True)

        if converted_tuple is None:  # If the given reference set is too small
            labels = sorted(int(data_series.unique()))  # The unique value in the dataset will be the label
            converted_series, bins = data_series, sorted(int(data_series.unique()))
        else:
            labels = range(deciles_value)
            converted_series, bins = converted_tuple
    return converted_series, labels, bins
