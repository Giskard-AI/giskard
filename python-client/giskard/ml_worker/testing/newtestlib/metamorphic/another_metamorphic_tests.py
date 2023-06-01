from giskard.ml_worker.testing.newtestlib.lib import BaseModel, test


@test()
def another_meta_test(model: BaseModel):
    return f"RUN: {__name__}"
