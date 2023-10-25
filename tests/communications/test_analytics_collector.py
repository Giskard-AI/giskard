from mixpanel import Consumer

from giskard.utils.analytics_collector import GiskardAnalyticsCollector


def test_tracking_doesnt_throw_errors():
    ac = GiskardAnalyticsCollector()
    ac.mp._consumer = Consumer(events_url="https://invalid.url")
    ac.track("test")
