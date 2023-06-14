from unittest.mock import MagicMock
import pandas as pd
from pytest import approx
from giskard import Model, Dataset, slicing_function
from giskard.scanner.calibration.issues import CalibrationIssueInfo, OverconfidenceIssue, UnderconfidenceIssue


def test_underconfidence_issue_exports_test():
    data = MagicMock(Dataset)
    model = MagicMock(Model)

    @slicing_function(row_level=False)
    def my_slice(df):
        return df.head(10)

    info = CalibrationIssueInfo(
        my_slice,
        10,
        metric_value_slice=0.3,
        metric_value_reference=0.1,
        loss_values=pd.Series(),
        fail_idx=[],
        threshold=0.8,
        p_threshold=0.81,
    )
    issue = UnderconfidenceIssue(model, data, "major", info)

    tests = issue.generate_tests()

    assert len(tests) == 1

    the_test = tests[0]

    assert the_test.meta.name == "test_underconfidence_rate"
    assert the_test.params["model"] == model
    assert the_test.params["dataset"] == data
    assert the_test.params["p_threshold"] == approx(0.81)
    assert the_test.params["slicing_function"] == my_slice

    # Global rate is 10% (`metric_value_reference`), we accept a 80% deviation, thus up to 18%:
    assert the_test.params["threshold"] == approx(0.18)


def test_overconfidence_issue_exports_test():
    data = MagicMock(Dataset)
    model = MagicMock(Model)

    @slicing_function(row_level=False)
    def my_slice(df):
        return df.head(10)

    info = CalibrationIssueInfo(
        my_slice,
        10,
        metric_value_slice=0.3,
        metric_value_reference=0.15,
        loss_values=pd.Series(),
        fail_idx=[],
        threshold=0.10,
        p_threshold=0.5,
    )
    issue = OverconfidenceIssue(model, data, "major", info)

    tests = issue.generate_tests()

    assert len(tests) == 1

    the_test = tests[0]

    assert the_test.meta.name == "test_overconfidence_rate"
    assert the_test.params["model"] == model
    assert the_test.params["dataset"] == data
    assert the_test.params["p_threshold"] == approx(0.5)
    assert the_test.params["slicing_function"] == my_slice

    # Global rate is 15% (`metric_value_reference`), we accept a 10% deviation, thus up to 16.5%:
    assert the_test.params["threshold"] == approx(0.165)
