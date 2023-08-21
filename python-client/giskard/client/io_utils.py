"""Various input/output utility functions"""

import re
from io import BytesIO
from typing import Any, Optional

import cloudpickle
import pandas as pd
from zstandard import ZstdCompressor, ZstdDecompressor

COMPRESSION_MAX_OUTPUT_SIZE = 10**9  # 1GB


def pickle_dumps(variable: object) -> bytes:
    pickle: bytes = cloudpickle.dumps(variable)
    return pickle


def pickle_loads(dumped_pickle: bytes) -> Any:
    return cloudpickle.loads(dumped_pickle)


def load_decompress(serialized: bytes) -> Any:
    return pickle_loads(decompress(serialized))


def save_df(df: pd.DataFrame, format: str = "csv") -> bytes:
    pandas_version: int = int(re.sub(r"\D", "", pd.__version__))
    if format == "csv":
        import csv

        csv_buffer = BytesIO()
        if pandas_version >= 120:
            df.to_csv(csv_buffer, index=False, na_rep="_GSK_NA_", escapechar="\\", quoting=csv.QUOTE_NONNUMERIC)
        else:
            csv_buffer.write(
                df.to_csv(index=False, na_rep="_GSK_NA_", escapechar="\\", quoting=csv.QUOTE_NONNUMERIC).encode("utf-8")
            )
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
    # elif compression == "lz4":
    #     import lz4.frame
    #     data = lz4.frame.compress(data, compression_level=3, content_checksum=True)
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
