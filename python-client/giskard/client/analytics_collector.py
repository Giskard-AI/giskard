import hashlib
import os
import uuid

from mixpanel import Consumer, Mixpanel


def nofail(func):
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
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
    def __init__(self) -> None:
        self.mp = self.configure_mixpanel()
        self.is_enabled = False
        self.distinct_user_id = None

    @staticmethod
    @nofail
    def configure_mixpanel():
        is_dev_mode = os.environ.get("GISKARD_DEV_MODE", "n").lower() in ["yes", "true", "1"]
        dev_mp_project_key = "4cca5fabca54f6df41ea500e33076c99"
        prod_mp_project_key = "2c3efacc6c26ffb991a782b476b8c620"

        return Mixpanel(
            dev_mp_project_key if is_dev_mode else prod_mp_project_key,
            consumer=Consumer(api_host="pxl.giskard.ai"),
        )

    @nofail
    def init(self, server_settings):
        giskard_instance_id = server_settings.get("app").get("generalSettings").get("instanceId")
        self.is_enabled = (
            server_settings.get("app").get("generalSettings").get("isAnalyticsEnabled")
        )
        user_login = server_settings.get("user").get("user_id")
        anonymous_login = anonymize(user_login)
        self.distinct_user_id = f"{giskard_instance_id}-{anonymous_login}"

        if self.is_enabled:
            self.mp.people_set(
                self.distinct_user_id,
                {
                    "Giskard Instance": giskard_instance_id,
                    "Giskard Version": server_settings.get("app").get("version"),
                },
            )

    @nofail
    def track(self, event_name, properties=None, meta=None, force=False):
        if self.is_enabled or force:
            self.mp.track(
                distinct_id=self.distinct_user_id or self.machine_based_user_id(),
                event_name=event_name,
                properties=properties,
                meta=meta,
            )

    @staticmethod
    def machine_based_user_id():
        return anonymize(str(uuid.getnode()) + os.getlogin())
