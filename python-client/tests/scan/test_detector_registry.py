from giskard.scanner.registry import DetectorRegistry
from giskard.scanner.decorators import detector


def test_detector_registry():
    class MyTestDetector:
        def run(self, model, dataset):
            return []

    DetectorRegistry.register("test_detector", MyTestDetector, tags=["tag_1", "tag_2", "classification"])

    assert "test_detector" in DetectorRegistry.get_detector_classes().keys()
    assert DetectorRegistry.get_detector_classes()["test_detector"] == MyTestDetector
    assert DetectorRegistry.get_detector_classes(tags=["tag_1"])["test_detector"] == MyTestDetector
    assert "test_detector" not in DetectorRegistry.get_detector_classes(tags=["regression"]).keys()


def test_detector_decorator():
    @detector
    class MyDecoratedDetector:
        def run(self, model, dataset):
            return []

    assert "my_decorated_detector" in DetectorRegistry.get_detector_classes().keys()

    @detector(name="other_detector", tags=["tag_1", "tag_2"])
    class MyOtherDecoratedDetector:
        def run(self, model, dataset):
            return []

    assert "other_detector" in DetectorRegistry.get_detector_classes().keys()
    assert "other_detector" in DetectorRegistry.get_detector_classes(tags=["tag_2"]).keys()
    assert "other_detector" not in DetectorRegistry.get_detector_classes(tags=["regression"]).keys()
