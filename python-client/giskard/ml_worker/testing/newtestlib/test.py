from giskard import test
from giskard.ml_worker.testing.registry.lib import BaseModel, Dataset


# @test(inputs={
#     'test_dataset': {
#         'requirements': {TARGET_DEFINED}
#     }
# })
# def my_test(model: BaseModel, train_dataset: Dataset, test_dataset: Dataset):
#     print('my_test')
#
#


@test()
def metamorphic_test(model: BaseModel, train_dataset: Dataset, test_dataset: Dataset):
    print("metamorphic_test")
    return f"RUN: {__name__}"
