from giskard.scanner.data_leakage.data_leakage_detector import DataLeakageDetector, DataLeakageIssue


def test_data_leakage_is_detected(enron_data, enron_model):
    detector = DataLeakageDetector()
    issues = detector.run(enron_model, enron_data)

    # should detect no issue
    assert len(issues) == 0

    # Now we add normalization problems
    ll = len(enron_data)

    def renormalize_df(df):
        numeric_cols = df.select_dtypes("number").columns
        df.loc[:, numeric_cols] /= ll / len(df)
        return df

    _prev_func = enron_model.data_preprocessing_function
    enron_model.data_preprocessing_function = renormalize_df
    issues = detector.run(enron_model, enron_data)

    assert len(issues) == 1
    assert isinstance(issues[0], DataLeakageIssue)

    enron_model.data_preprocessing_function = _prev_func


def test_data_leakage_works_on_small_dataset(enron_data, enron_model):
    test_data_leakage_is_detected(enron_data.slice(lambda df: df.sample(10), row_level=False), enron_model)
