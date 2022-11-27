import pandas as pd

from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.utils.logging import timer
from enum import Enum

class Direction(Enum):
    Invariant = 0
    Increasing = 1
    Decreasing = -1

def ge_result_to_test_result(result, passed=True) -> SingleTestResult:
    """
        Converts a result of Great Expectations to TestResultMessage - java/python bridge test result class
    :param passed: boolean flag containing result of a test
    :param result: Great Expectations result
    :return: TestResultMessage - a protobuf generated test result class
    """

    return SingleTestResult(
        passed=passed,
        actual_slices_size=[result["element_count"]],
        missing_count=result["missing_count"],
        missing_percent=result["missing_percent"],
        unexpected_count=result["unexpected_count"],
        unexpected_percent=result["unexpected_percent"],
        unexpected_percent_total=result["unexpected_percent_total"],
        unexpected_percent_nonmissing=result["unexpected_percent_nonmissing"],
        partial_unexpected_index_list=result["partial_unexpected_index_list"],
        unexpected_index_list=result["unexpected_index_list"],
    )


@timer("Perturb data")
def apply_perturbation_inplace(df: pd.DataFrame, perturbation_dict):
    modified_rows = []
    i = 0
    for idx, r in df.iterrows():
        added = False
        for pert_col, pert_func in perturbation_dict.items():
            original_value = r[pert_col]
            new_value = pert_func(r)
            if original_value != new_value and not added:
                added = True
                modified_rows.append(i)
                df.loc[idx, pert_col] = new_value
        i += 1
    return modified_rows
