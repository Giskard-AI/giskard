from typing import Any, Dict, List, Optional

import logging
from pickle import PicklingError

import cloudpickle
from xxhash import xxh3_128_hexdigest

LOGGER = logging.getLogger(__name__)

SEED = 42


class SimpleCache:
    """
    Simple cache for storing and retrieving results. Uses the LRU algorithm.
    """

    def __init__(self, max_results: int = 128):
        """
        Initialize the cache with a maximum number of results.

        Args:
            max_results (int): The maximum number of results to store in the cache.
        """
        self._max_results = max_results
        self._results: Optional[Dict[str, Any]] = None
        self._keys: Optional[List[str]] = None

    def content(self):
        """
        Returns the content of the cache.
        """
        return self._results, self._keys

    def start(self, cache_content: Dict[str, Any], cache_keys: List[str]):
        """
        Initialize the cache with existing content and keys.

        Args:
            cache_content (dict): The content to populate the cache.
            cache_keys (list): The keys associated with the cache content.
        """
        self._results = cache_content
        self._keys = cache_keys

    @staticmethod
    def _generate_key(key: str):
        if not isinstance(key, str):
            raise ValueError(f"Key should be an string, got '{type(key)}' for {key}")
        return xxh3_128_hexdigest(key, seed=SEED)

    def add_result(self, key: str, result: Any) -> None:
        """
        Add a result to the cache.

        Args:
            obj: The key object to identify the object to cache.
            result: The result to be cached.
        """
        obj_hash = self._generate_key(key)
        # Using cloudpickle instead of default pickle here
        self._results[obj_hash] = cloudpickle.dumps(result)
        if obj_hash in self._keys:
            self._keys.remove(obj_hash)
        self._keys.insert(0, obj_hash)

        # If the cache is full, remove the least recently used item
        if len(self._results) > self._max_results:
            removed_key = self._keys.pop()
            self._results.pop(removed_key)

    def safe_add_result(self, key: str, result: Any):
        """
        Add a result to the cache safely, handling exceptions.

        Args:
            obj: The key object to identify the object to cache.
            result: The result to be cached.

        Returns:
            bool: True if the result was added successfully, False otherwise.
        """
        try:
            self.add_result(key, result)
            return True
        except (AttributeError, PicklingError):
            LOGGER.exception("Error while trying to add to cache", exc_info=True)
            return False

    def get_result(self, key: str):
        """
        Retrieve a result from the cache.

        Args:
            obj: The key for the result.

        Returns:
            Tuple[bool, Any]: A tuple with a boolean indicating whether the result was found
            in the cache and the result itself.
        """
        obj_hash = self._generate_key(key)

        if obj_hash in self._results:
            self._keys.remove(obj_hash)
            self._keys.insert(0, obj_hash)
            return True, cloudpickle.loads(self._results[obj_hash])
        else:
            return False, None


CACHE = SimpleCache()
