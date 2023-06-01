import hashlib
import os
import uuid
from functools import wraps
from typing import Dict

from mixpanel import Consumer, Mixpanel

from giskard.settings import settings


def analytics_method(f):
    """
        Only runs a decorated function if analytics is enabled and swallows the errors
    """

    @wraps(f)
    def inner_function(*args, **kwargs):
        try:
            if not settings.disable_analytics:
                return f(*args, **kwargs)
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
    dev_mp_project_key = "4cca5fabca54f6df41ea500e33076c99"
    prod_mp_project_key = "2c3efacc6c26ffb991a782b476b8c620"
    server_info: Dict = None
    mp: Mixpanel

    def __init__(self) -> None:
        self.is_enabled = not settings.disable_analytics
        if self.is_enabled:
            self.mp = self.configure_mixpanel()
            self.distinct_user_id = GiskardAnalyticsCollector.machine_based_user_id()

    @staticmethod
    @analytics_method
    def configure_mixpanel() -> Mixpanel:
        is_dev_mode = os.environ.get("GISKARD_DEV_MODE", "n").lower() in ["yes", "true", "1"]

        return Mixpanel(
            GiskardAnalyticsCollector.dev_mp_project_key if is_dev_mode else
            GiskardAnalyticsCollector.prod_mp_project_key,
            consumer=Consumer(api_host="pxl.giskard.ai"),
        )

    @analytics_method
    def init_server_info(self, server_info):
        self.server_info = {
            "Server instance": server_info.get("instanceId"),
            "Server version": server_info.get("serverVersion"),
            "Server license": server_info.get("instanceLicenseId"),
            "Giskard User": server_info.get("user"),
        }

    @analytics_method
    def track(self, event_name, properties=None, meta=None, force=False):
        if self.is_enabled or force:
            merged_props = []
            if properties is not None:
                merged_props += properties.items()
            if self.server_info is not None:
                merged_props += self.server_info.items()

            self.mp.track(
                distinct_id=self.distinct_user_id,
                event_name=event_name,
                properties=dict(merged_props),
                meta=meta,
            )

    @staticmethod
    def machine_based_user_id():
        try:
            return anonymize(str(uuid.getnode()) + os.getlogin())
        except BaseException:  # noqa
            # https://bugs.python.org/issue40821
            return "unknown"


analytics = GiskardAnalyticsCollector()
