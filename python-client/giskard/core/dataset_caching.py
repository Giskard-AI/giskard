from xxhash import xxh3_128_hexdigest

from giskard.datasets.base import Dataset, GISKARD_HASH_COLUMN


def generate_row_hashes(dataset: Dataset):
    df = dataset.df

    if GISKARD_HASH_COLUMN in df:
        unknown_values = list(df[GISKARD_HASH_COLUMN].isna())
        df.loc[unknown_values, GISKARD_HASH_COLUMN] = list(
            map(lambda row: xxh3_128_hexdigest(f"({', '.join(map(lambda x: str(x), row))}".encode('utf-8')),
                df.loc[unknown_values][dataset.columns].values))
    else:
        df[GISKARD_HASH_COLUMN] = list(
            map(lambda row: xxh3_128_hexdigest(f"({', '.join(map(lambda x: str(x), row))}".encode('utf-8')),
                df[dataset.columns].values))
