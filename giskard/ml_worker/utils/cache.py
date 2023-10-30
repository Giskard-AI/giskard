from typing import Any, Dict, List, Optional

import hashlib
import logging
from collections import OrderedDict
from pickle import PicklingError

LOGGER = logging.getLogger(__name__)


class SimpleCache:
    def __init__(self, max_results=128):
        # self.results = OrderedDict()
        self.max_results = max_results
        self._results: Optional[Dict[str, Any]] = None
        self._keys: Optional[List[str]] = None

    def start(self, cache_content: Dict[str, Any], cache_keys: List[str]):
        self._results = cache_content
        self._keys = cache_keys

    def content(self):
        return self._results, self._keys

    def add_result(self, obj, result):
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()
        self._results[obj_hash] = result
        self._keys.insert(0, obj_hash)
        # If the cache is full, remove the least recently used item
        if len(self._results) >= self.max_results:
            self._results.pop(self._keys.pop())

    def safe_add_result(self, obj, result):
        try:
            return self.add_result(obj, result)
        except (AttributeError, PicklingError) as e:
            LOGGER.warning("Error while trying to add to cache")
            LOGGER.exception(e)

    def get_result(self, obj):
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        if obj_hash in self._results:
            self._keys.remove(obj_hash)
            self._keys.insert(0, obj_hash)
            return True, self._results[obj_hash]
        else:
            return False, None


CACHE = SimpleCache()
