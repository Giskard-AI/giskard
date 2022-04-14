from generated.ml_worker_pb2 import SingleTestResult


def ge_result_to_test_result(result, passed=True) -> SingleTestResult:
    """
        Converts a result of Great Expectations to TestResultMessage - java/python bridge test result class
    :param result: Great Expectations result
    :return: TestResultMessage - a protobuf generated test result class
    """

    return SingleTestResult(
        passed=passed,
        element_count=result['element_count'],
        missing_count=result['missing_count'],
        missing_percent=result['missing_percent'],
        unexpected_count=result['unexpected_count'],
        unexpected_percent=result['unexpected_percent'],
        unexpected_percent_total=result['unexpected_percent_total'],
        unexpected_percent_nonmissing=result['unexpected_percent_nonmissing'],
        partial_unexpected_index_list=result['partial_unexpected_index_list'],
        # partial_unexpected_counts=result['partial_unexpected_counts'],
        unexpected_index_list=result['unexpected_index_list']
    )


def apply_perturbation_inplace(df, perturbation_dict):
    modified_rows = []
    for idx, r in df.iterrows():
        added = False
        for pert_col, pert_func in perturbation_dict.items():
            original_value = r[pert_col]
            new_value = pert_func(r)
            if original_value != new_value and not added:
                added = True
                modified_rows.append(idx)
                df.loc[idx, pert_col] = new_value
    return modified_rows
