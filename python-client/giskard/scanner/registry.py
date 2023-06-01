from collections import defaultdict


class DetectorRegistry:
    _detectors = dict()
    _tags = defaultdict(set)

    @classmethod
    def register(cls, name, detector, tags=None):
        cls._detectors[name] = detector
        if tags is not None:
            cls._tags[name] = set(tags)

    @classmethod
    def get_detector_classes(cls, tags=None) -> dict:
        if tags is None:
            return {n: d for n, d in cls._detectors.items()}

        return {n: d for n, d in cls._detectors.items() if cls._tags[n].intersection(tags)}
