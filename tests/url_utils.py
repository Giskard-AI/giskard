from pathlib import Path
from urllib.request import urlretrieve


def fetch_test_data(url: str, file: Path) -> None:
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)

    if not file.exists():
        urlretrieve(url, file)
