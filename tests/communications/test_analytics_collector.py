from mixpanel import Consumer

from giskard.utils.analytics_collector import GiskardAnalyticsCollector
from giskard.settings import settings


def test_tracking_doesnt_throw_errors():
    analytics_flag = settings.disable_analytics
    settings.disable_analytics = False
    ac = GiskardAnalyticsCollector()
    ac.mp._consumer = Consumer(events_url="https://invalid.url")
    ac.track("test")
    settings.disable_analytics = analytics_flag
