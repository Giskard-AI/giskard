import codecs
import datetime
import logging
import os
import re
import socket
from contextlib import closing

import requests

import giskard
from giskard.client.python_utils import warning

logger = logging.getLogger(__name__)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def readable_hex(data):
    if not os.environ.get("GSK_ML_WORKER_LOG_HEX", False):
        return ""
    s = codecs.encode(data, "hex").decode()
    return " ".join(s[i : i + 2] for i in range(0, len(s), 2))


def is_pre_release(current_version: str):
    # A very dummy pre-release checker, to be improved
    return re.match(r".*[a-z].*", current_version) is not None


def check_latest_giskard_version():
    try:
        current_version = giskard.__version__
        if not is_pre_release(current_version):
            return
        respose = requests.get("https://pypi.org/pypi/giskard/json", timeout=3).json()
        releases = respose.get("releases")
        releases_dates = {}
        if current_version not in releases:
            return
        for ver, resources in releases.items():
            latest_release_date = max(
                map(
                    lambda r: datetime.datetime.fromisoformat(r["upload_time"]),
                    resources,
                )
            )
            releases_dates[ver] = latest_release_date
        latest_version, latest_release_date = max(releases_dates.items(), key=lambda x: x[1])

        if latest_release_date > releases_dates[current_version]:
            warning(
                "You're using a pre-release version of giskard while a "
                "new version is available, please install it with: "
                f'pip install "giskard=={latest_version}"'
            )
    except BaseException as e:
        logger.exception("Failed to fetch latest giskard version", e)
