import concurrent.futures

import dill


def safe_fn(fn, /, *args, **kwargs):
    return dill.dumps(dill.loads(fn)(dill.loads(args), dill.loads(kwargs)))


class DillProcessPoolExecutor(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        self.executor = concurrent.futures.ProcessPoolExecutor(**self.kwargs)
        self.executor.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.executor.__exit__(type, value, traceback)
        return self

    def submit_and_wait(self, fn, /, *args, **kwargs):
        # Use dill to pickle and unpickle as it works with more object than pickle/cloudpickle
        return dill.loads(self.executor.submit(safe_fn, dill.dumps(fn), dill.dumps(args), dill.dumps(kwargs)).result())
