from typing import Any, Sequence

from giskard.scanner.decorators import detector
from giskard.scanner.registry import DetectorRegistry, Issue
from giskard.scanner.scanner import BaseScanner


class SomeModel:
    @property
    def model_type(self):
        return "new_domain"


class SomeDataset:
    ...


def test_external_detector():
    @detector(name="custom_detector", tags=["new_domain"])
    class CustomDetector:
        def run(self, model: Any, dataset: Any) -> Sequence[Issue]:
            return []  # empty list of issues

    assert "custom_detector" in DetectorRegistry.get_detector_classes(tags=["new_domain"]).keys()

    scanner = BaseScanner()

    model = SomeModel()
    dataset = SomeDataset()

    scanner.analyze(model, dataset)
