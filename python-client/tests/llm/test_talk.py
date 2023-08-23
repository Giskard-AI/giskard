from giskard.llm.talk.talk import ModelSpec


def test_predict(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    expected = german_credit_model.predict(
        german_credit_test_data.slice(lambda df: df.head(10), row_level=False)
    ).prediction

    for i in range(10):
        assert model_spec.predict(german_credit_test_data.df.iloc[i].to_json()) == expected[i]


def test_predict_missing_features(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert (
        model_spec.predict(german_credit_test_data.df.drop("credit_history", axis=1).iloc[0].to_json())
        == "ValueError(\"Required features `{'credit_history'}` are not provided.\")"
    )


def test_explain_missing_features(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model, dataset=german_credit_test_data)

    assert (
        model_spec.explain(german_credit_test_data.df.drop("job", axis=1).iloc[0].to_json())
        == "ValueError(\"Required features `{'job'}` are not provided.\")"
    )


def test_explain_missing_dataset(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert (
        model_spec.explain(german_credit_test_data.df.drop("job", axis=1).iloc[0].to_json())
        == "Explanation is not available since no dataset has been provided"
    )


def test_scan_result_info_missing_scan(german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert model_spec.scan_result_info() == "The model should be scanned with Giskard first"


def test_model_quality_missing_scan(german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert model_spec.model_quality() == "The model should be scanned with Giskard first"
