from pathlib import Path
from urllib.request import urlretrieve


def fetch_from_ftp(url: str, file: Path) -> None:
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)

    if not file.exists():
        urlretrieve(url, file)
