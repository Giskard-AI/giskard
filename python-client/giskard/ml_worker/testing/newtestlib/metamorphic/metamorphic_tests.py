from giskard.ml_worker.testing.newtestlib.lib import BaseModel, Dataset, test


@test()
def test_f1(model: BaseModel, dataset: Dataset):
    print("Test F1!!!")
    return f"RUN: {__name__}"
