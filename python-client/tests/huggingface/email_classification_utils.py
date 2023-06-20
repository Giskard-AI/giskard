import glob
import logging
import os
import tarfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def get_email_files():
    out_path = Path.home() / ".giskard"
    enron_path = out_path / "enron_with_categories"
    if not enron_path.exists():
        url = "http://bailando.sims.berkeley.edu/enron/enron_with_categories.tar.gz"
        logger.info(f"Downloading test data from: {url}")
        response = requests.get(url, stream=True)
        file = tarfile.open(fileobj=response.raw, mode="r|gz")
        os.makedirs(out_path, exist_ok=True)
        file.extractall(path=out_path)
    return [f.replace(".cats", "") for f in glob.glob(str(enron_path) + "/*/*.cats")]
