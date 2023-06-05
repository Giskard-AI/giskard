import hashlib
import os
import platform
import uuid
from functools import wraps
from threading import Lock
from typing import Dict, Optional

import requests
from mixpanel import Mixpanel

from giskard.settings import settings
from giskard.utils import threaded
from giskard.utils.environment_detector import EnvironmentDetector


def analytics_method(f):
    """
        Only runs a decorated function if analytics is enabled and swallows the errors
    """

    @wraps(f)
    def inner_function(*args, **kwargs):
        try:
            if not settings.disable_analytics:
                return f(*args, **kwargs)
        except BaseException as e:  # NOSONAR
            try:
                analytics.track('tracking error', {'error': str(e)})
            except BaseException:  # NOSONAR
                pass

    return inner_function


def anonymize(message):
    if not message:
        return None
    if isinstance(message, list):
        return [anonymize(m) for m in message]

    return hashlib.sha1(str(message).encode()).hexdigest()[:10]


class GiskardAnalyticsCollector:
    lock = Lock()
    ip: Optional[str]
    dev_mp_project_key = "4cca5fabca54f6df41ea500e33076c99"
    prod_mp_project_key = "2c3efacc6c26ffb991a782b476b8c620"
    server_info: Dict = None
    mp: Mixpanel
    giskard_version: Optional[str]
    environment: str

    def __init__(self) -> None:
        self.is_enabled = not settings.disable_analytics
        self.giskard_version = None
        self.ip = None
        self.environment = EnvironmentDetector().detect()
        if self.is_enabled:
            self.mp = self.configure_mixpanel()
            self.distinct_user_id = GiskardAnalyticsCollector.machine_based_user_id()

    @staticmethod
    @analytics_method
    def configure_mixpanel() -> Mixpanel:
        is_dev_mode = os.environ.get("GISKARD_DEV_MODE", "n").lower() in ["yes", "true", "1"]

        return Mixpanel(
            GiskardAnalyticsCollector.dev_mp_project_key if is_dev_mode else
            GiskardAnalyticsCollector.prod_mp_project_key
        )

    @analytics_method
    def init_server_info(self, server_info):
        self.server_info = {
            "Server instance": server_info.get("instanceId"),
            "Server version": server_info.get("serverVersion"),
            "Server license": server_info.get("instanceLicenseId"),
            "Giskard User": server_info.get("user"),
        }

    @threaded
    @analytics_method
    def track(self, event_name, properties=None, meta=None, force=False):
        if not self.giskard_version:
            import giskard
            self.giskard_version = giskard.get_version()
        if not self.ip:
            self.initialize_geo()
        if self.is_enabled or force:
            merged_props = {
                "giskard_version": self.giskard_version,
                "python_version": platform.python_version(),
                "ip": self.ip,  # only for aggregated stats: city, country, region. IP itself isn't stored
                "arch": platform.machine(),
                "$os": platform.system(),
                "os-full": platform.platform(aliased=True),
                "environment": self.environment
            }
            if properties is not None:
                merged_props = {**merged_props, **properties}
            if self.server_info is not None:
                merged_props = {**merged_props, **self.server_info}

            self.mp.track(
                distinct_id=self.distinct_user_id,
                event_name=event_name,
                properties=dict(merged_props),
                meta=meta
            )

    @staticmethod
    def machine_based_user_id():
        try:
            return anonymize(str(uuid.getnode()) + os.getlogin())
        except BaseException:  # noqa
            # https://bugs.python.org/issue40821
            return "unknown"

    def initialize_geo(self):
        """
        Query a user's IP address to convert it to an aggregated telemetry:
            - city
            - region
            - country
        IP address itself **isn't stored** by in the telemetry data
        """
        with GiskardAnalyticsCollector.lock:
            if self.ip:
                return
            try:
                self.ip = requests.get('http://ip-api.com/json').json().get('query', 'unknown')
            except:  # noqa
                self.ip = "unknown"


analytics = GiskardAnalyticsCollector()
