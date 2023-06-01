from contextlib import AbstractContextManager
from .cache import ModelCache

# This is a global switch that controls model prediction cache.
_cache_enabled = True


def set_cache_enabled(value: bool):
    global _cache_enabled
    _cache_enabled = value


def get_cache_enabled():
    global _cache_enabled
    return _cache_enabled


def enable_cache():
    set_cache_enabled(True)


def disable_cache():
    set_cache_enabled(False)


class no_cache(AbstractContextManager):
    def __init__(self):
        self.prev = get_cache_enabled()

    def __enter__(self):
        set_cache_enabled(False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_cache_enabled(self.prev)


__all__ = ["set_cache_enabled", "get_cache_enabled", "enable_cache", "disable_cache", "no_cache", "ModelCache"]
