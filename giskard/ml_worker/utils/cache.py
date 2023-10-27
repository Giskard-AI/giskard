import hashlib
from collections import OrderedDict


class SimpleCache:
    def __init__(self, max_results=128):
        self.results = OrderedDict()
        self.max_results = max_results

    def add_result(self, obj, result):
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        # If the cache is full, remove the least recently used item
        if len(self.results) >= self.max_results:
            self.results.popitem(last=False)

        self.results[obj_hash] = result

    def get_result(self, obj):
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        if obj_hash in self.results:
            self.results.move_to_end(obj_hash)
            return self.results[obj_hash]
        else:
            return None
