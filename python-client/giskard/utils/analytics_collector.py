import hashlib
import os
import platform
import time
import uuid
from dataclasses import dataclass
from functools import wraps
from queue import Queue
from threading import Lock
from typing import Dict, Optional, Any

import requests
from mixpanel import Mixpanel

from giskard.settings import settings
from giskard.utils import fullname, threaded
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


def get_model_properties(model):
    from ..models.base import WrapperModel

    if model is None:
        return {}

    inner_model_class = fullname(model.model) if isinstance(model, WrapperModel) else None
    feature_names = [anonymize(n) for n in model.meta.feature_names]

    return {
        "model_id": str(model.id),
        "model_type": model.meta.model_type.value,
        "model_class": fullname(model),
        "model_inner_class": inner_model_class,
        "model_feature_names": feature_names,
    }


def get_dataset_properties(dataset):
    if dataset is None:
        return {}

    column_types = {anonymize(k): v for k, v in dataset.column_types.items()} if dataset.column_types else {}
    column_dtypes = {anonymize(k): v for k, v in dataset.column_dtypes.items()}

    return {
        "dataset_id": str(dataset.id) if dataset is not None else "none",
        "dataset_rows": dataset.df.shape[0],
        "dataset_cols": dataset.df.shape[1],
        "dataset_column_types": column_types,
        "dataset_column_dtypes": column_dtypes,
    }


@dataclass
class TelemetryMessage:
    event_name: Any
    properties: Any
    meta: Any


class GiskardAnalyticsCollector:
    is_consuming: bool = False
    geo_lock = Lock()
    consume_lock = Lock()
    ip: Optional[str]
    dev_mp_project_key = "4cca5fabca54f6df41ea500e33076c99"
    prod_mp_project_key = "2c3efacc6c26ffb991a782b476b8c620"
    server_info: Optional[Dict] = None
    mp: Mixpanel
    giskard_version: Optional[str]
    environment: str
    queue: Queue[TelemetryMessage] = Queue()

    def __init__(self) -> None:
        self.is_enabled = not settings.disable_analytics
        self.giskard_version = None
        self.ip = None
        self.environment = EnvironmentDetector().detect()
        if self.is_enabled:
            self.mp = self.configure_mixpanel()
            self.distinct_user_id = GiskardAnalyticsCollector.machine_based_user_id()

    @threaded
    def _consume(self):
        with self.consume_lock:
            self.is_consuming = True
            while not self.queue.empty():
                event = self.queue.get(block=True)
                self.mp.track(
                    distinct_id=self.distinct_user_id,
                    event_name=event.event_name,
                    properties=event.properties,
                    meta=event.meta
                )
                # in case of very frequent requests make a pause between them
                time.sleep(0.2)
            self.is_consuming = False

    def _submit(self, msg):
        self.queue.put(msg, block=True)

    @staticmethod
    @analytics_method
    def configure_mixpanel() -> Mixpanel:
        is_dev_mode = os.environ.get("GISKARD_DEV_MODE", "n").lower() in ["yes", "true", "1"]

        return Mixpanel(
            GiskardAnalyticsCollector.dev_mp_project_key
            if is_dev_mode
            else GiskardAnalyticsCollector.prod_mp_project_key
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

            self._submit(TelemetryMessage(
                event_name=event_name, properties=dict(merged_props), meta=meta
            ))

            if not self.is_consuming:
                self._consume()

    @staticmethod
    def machine_based_user_id():
        try:
            return anonymize(str(uuid.getnode()) + os.getlogin())
        except BaseException:  # noqa NOSONAR
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
        with GiskardAnalyticsCollector.geo_lock:
            if self.ip:
                return
            try:
                self.ip = requests.get('http://ip-api.com/json').json().get('query', 'unknown')  # noqa NOSONAR
            except:  # noqa NOSONAR
                self.ip = "unknown"


analytics = GiskardAnalyticsCollector()
