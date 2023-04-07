import hashlib
import random
import uuid

import cloudpickle


def generate_func_id(name) -> str:
    rd = random.Random()
    rd.seed(hashlib.sha512(name.encode('utf-8')).hexdigest())
    func_id = str(uuid.UUID(int=rd.getrandbits(128), version=4))
    return str(func_id)


def get_func_uuid(func) -> str:
    func_name = f"{func.__module__}.{func.__name__}"

    if func_name.startswith('__main__'):
        reference = cloudpickle.dumps(func)
        func_name += hashlib.sha512(reference).hexdigest()

    return generate_func_id(func_name)
