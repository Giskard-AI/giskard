import hashlib
import logging
from pickle import PicklingError
from typing import Optional, Dict, Any, List

LOGGER = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple cache for storing and retrieving results. Uses the LRU algorithm.
    """

    def __init__(self, max_results=128):
        """
        Initialize the cache with a maximum number of results.

        Args:
            max_results (int): The maximum number of results to store in the cache.
        """
        self.max_results = max_results
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

    def add_result(self, obj, result):
        """
        Add a result to the cache.

        Args:
            obj: The key for the result.
            result: The result to be cached.
        """
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()
        self._results[obj_hash] = result
        self._keys.insert(0, obj_hash)

        # If the cache is full, remove the least recently used item
        if len(self._results) >= self.max_results:
            removed_key = self._keys.pop()
            self._results.pop(removed_key)

    def safe_add_result(self, obj, result):
        """
        Add a result to the cache safely, handling exceptions.

        Args:
            obj: The key for the result.
            result: The result to be cached.

        Returns:
            bool: True if the result was added successfully, False otherwise.
        """
        try:
            self.add_result(obj, result)
            return True
        except (AttributeError, PicklingError) as e:
            LOGGER.warning("Error while trying to add to cache")
            LOGGER.exception(e)
            return False

    def get_result(self, obj):
        """
        Retrieve a result from the cache.

        Args:
            obj: The key for the result.

        Returns:
            Tuple[bool, Any]: A tuple with a boolean indicating whether the result was found
            in the cache and the result itself.
        """
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        if obj_hash in self._results:
            self._keys.remove(obj_hash)
            self._keys.insert(0, obj_hash)
            return True, self._results[obj_hash]
        else:
            return False, None


CACHE = SimpleCache()
