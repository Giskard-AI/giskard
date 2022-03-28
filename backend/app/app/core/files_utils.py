import cloudpickle
import pandas as pd
from io import BytesIO

from zstandard import ZstdDecompressor


def read_dataset_file(file_path: str) -> pd.DataFrame:
    try:
        df = pd.DataFrame()
        dzst = ZstdDecompressor()
        with open(file_path, "rb") as f:
            bytes_io = BytesIO(dzst.decompress(f.read()))
        if ".csv" in file_path:
            df = pd.read_csv(bytes_io)
        elif ".xls" in file_path:
            df = pd.read_excel(bytes_io)
        return df
    except Exception as e:
        raise e


def read_model_file(file_path: str) -> object:
    dzst = ZstdDecompressor()
    with open(file_path, "rb") as f:
        return cloudpickle.loads(dzst.decompress(f.read()))
