import hashlib


class SimpleCache:
    def __init__(self, max_results=20):
        self.results = {}
        self.order = []  # To maintain the order in which results were added
        self.max_results = max_results

    def add_result(self, obj, result):
        # Calculate the hash of the object
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        # Store the result with the object's hash as the key
        self.results[obj_hash] = result

        # Add the object's hash to the order list and remove the oldest result if necessary
        self.order.append(obj_hash)
        if len(self.order) > self.max_results:
            oldest_obj_hash = self.order.pop(0)
            del self.results[oldest_obj_hash]

    def get_result(self, obj):
        # Calculate the hash of the object
        obj_hash = hashlib.md5(repr(obj).encode()).hexdigest()

        # Return the result for the given object if it exists
        return self.results.get(obj_hash)