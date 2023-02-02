from giskard.ml_worker.testing.newtestlib.lib import Model, test


@test()
def another_meta_test(model: Model):
    return f"RUN: {__name__}"
