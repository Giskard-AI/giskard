from giskard.llm.talk.talk import ModelSpec


def test_predict(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model, datasets=german_credit_test_data)

    expected = german_credit_model.predict(german_credit_test_data).prediction

    for i in range(10):
        assert model_spec.predict(german_credit_test_data.df.iloc[i].to_json()) == expected[i]


def test_predict_missing_features(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model, datasets=german_credit_test_data)

    assert (
        model_spec.predict(german_credit_test_data.df.drop("credit_history", axis=1).iloc[0].to_json())
        == "ValueError(\"Required features `{'credit_history'}` are not provided.\")"
    )
