import pytest
from mixpanel import Consumer

from giskard.settings import settings
from giskard.utils.analytics_collector import GiskardAnalyticsCollector, analytics_method


class EnableAnalytics:
    """
    Context manager to enable/disable analytics on demand, disregarding the global settings
    """
    def __init__(self, do_enable=True):
        self.new_value = do_enable
        self.original_value = settings.disable_analytics

    def __enter__(self):
        settings.disable_analytics = not self.new_value

    def __exit__(self, exc_type, exc_val, exc_tb):
        settings.disable_analytics = self.original_value


def test_tracking_doesnt_throw_errors():
    with EnableAnalytics():
        ac = GiskardAnalyticsCollector()
        ac.mp._consumer = Consumer(events_url="https://invalid.url")
        ac.track("test")


def test_analytics_method():
    def no_exception():
        return "OK"

    def exception():
        raise RuntimeError("KO")

    with EnableAnalytics():
        assert analytics_method(no_exception)() == "OK"
        with pytest.raises(RuntimeError, match="KO"):
            assert analytics_method(exception())()

    with EnableAnalytics(False):
        assert analytics_method(no_exception)() is None
        assert analytics_method(exception)() is None
