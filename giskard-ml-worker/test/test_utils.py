import logging
from functools import wraps
from time import time


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logging.info(f'func:{f.__name__} args:[{args},{kw}] took: {te - ts:.2f}s')
        return result

    return wrap
