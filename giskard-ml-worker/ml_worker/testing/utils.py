from generated.ml_worker_pb2 import SingleTestResult
from zstandard import ZstdCompressor, ZstdDecompressor
from typing import Optional
from io import BytesIO
import re
import pandas as pd

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
        # partial_unexpected_counts=result['partial_unexpected_counts'],
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
    pandas_version: int = int(re.sub("[^0-9]", "", pd.__version__))
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


def bin_numerical_values(data_series):
    deciles_value = int(0.1 * len(data_series))
    converted_series = pd.qcut(data_series, deciles_value, labels=range(deciles_value))

    return converted_series
