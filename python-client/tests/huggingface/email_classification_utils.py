import glob
import os
import requests
import tarfile
from pathlib import Path


def get_email_files():
    url = "http://bailando.sims.berkeley.edu/enron/enron_with_categories.tar.gz"
    response = requests.get(url, stream=True)
    file = tarfile.open(fileobj=response.raw, mode="r|gz")
    out_path = Path.home() / ".giskard"
    os.makedirs(out_path, exist_ok=True)
    file.extractall(path=out_path)
    enron_path = str(out_path / "enron_with_categories")
    return [f.replace('.cats', '') for f in glob.glob(enron_path+'/*/*.cats')]
