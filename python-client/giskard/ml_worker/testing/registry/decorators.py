from giskard.ml_worker.testing.registry.registry import tests_registry


def test(_fn=None, name=None, tags=None):
    if _fn is not None:
        tests_registry.register(_fn)
        return _fn

    def inner(func):
        tests_registry.register(func, name=name, tags=tags)
        return func

    return inner
