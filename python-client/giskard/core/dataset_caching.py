import hashlib

from giskard.datasets.base import Dataset, GISKARD_HASH_COLUMN, GISKARD_COLUMN_PREFIX


def generate_row_hashes(dataset: Dataset):
    df = dataset.df
    non_giskard_column = [col for col in df.columns if not col.startswith(GISKARD_COLUMN_PREFIX)]

    if GISKARD_HASH_COLUMN in df:
        unknown_values = list(df[GISKARD_HASH_COLUMN].isna())
        df.loc[unknown_values, GISKARD_HASH_COLUMN] = df.loc[unknown_values][non_giskard_column].apply(
            lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest(), axis=1)
    else:
        df[GISKARD_HASH_COLUMN] = df[non_giskard_column].apply(
            lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest(), axis=1)
