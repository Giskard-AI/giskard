from giskard.ml_worker.testing.newtestlib.lib import Model, Dataset, test


@test()
def test_f1(model: Model, dataset: Dataset):
    print("Test F1!!!")
    return f"RUN: {__name__}"
