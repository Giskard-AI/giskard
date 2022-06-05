import logging
import re

import grpc
import pandas as pd
from eli5.lime import TextExplainer

from generated.ml_worker_pb2 import ExplainResponse, ExplainTextResponse
from generated.ml_worker_pb2 import RunTestRequest, TestResultMessage, RunModelResponse, RunModelRequest, DataFrame, \
    DataRow, RunModelForDataFrameResponse, RunModelForDataFrameRequest, ExplainRequest, ExplainTextRequest
from generated.ml_worker_pb2_grpc import MLWorkerServicer
from ml_worker.core.model_explanation import explain, text_explanation_prediction_wrapper, parse_text_explainer_response
from ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from ml_worker.utils.grpc_mapper import deserialize_model, deserialize_dataset

logger = logging.getLogger()


class MLWorkerServiceImpl(MLWorkerServicer):
    def __init__(self) -> None:
        super().__init__()

    def runTest(self, request: RunTestRequest, context: grpc.ServicerContext) -> TestResultMessage:
        from ml_worker.testing.functions import GiskardTestFunctions

        model = deserialize_model(request.model)

        tests = GiskardTestFunctions()
        _globals = {
            'model': model,
            'tests': tests
        }
        if request.reference_ds.serialized_df:
            _globals['reference_ds'] = deserialize_dataset(request.reference_ds)
        if request.actual_ds.serialized_df:
            _globals['actual_ds'] = deserialize_dataset(request.actual_ds)
        try:
            exec(request.code, _globals)
        except NameError as e:
            missing_name = re.findall(r"name '(\w+)' is not defined", str(e))[0]
            if missing_name == 'reference_ds':
                raise IllegalArgumentError("Reference Dataset is not specified")
            if missing_name == 'actual_ds':
                raise IllegalArgumentError("Actual Dataset is not specified")
            raise e

        return TestResultMessage(results=tests.tests_results)

    def explain(self, request: ExplainRequest, context) -> ExplainResponse:
        model = deserialize_model(request.model)
        dataset = deserialize_dataset(request.dataset)
        explanations = explain(model, dataset, request.columns)

        return ExplainResponse(explanations={k: ExplainResponse.Explanation(per_feature=v) for k, v in
                                             explanations['explanations'].items()})

    def explainText(self, request: ExplainTextRequest, context) -> ExplainTextResponse:
        n_samples = 500 if request.n_samples <= 0 else request.n_samples
        model = deserialize_model(request.model)
        text_column = request.feature_name

        if request.feature_types[text_column] != "text":
            raise ValueError(f"Column {text_column} is not of type text")
        text_document = request.features[text_column]
        input_df = pd.DataFrame({k: [v] for k, v in request.features.items()})[model.feature_names]
        text_explainer = TextExplainer(random_state=42, n_samples=n_samples)
        prediction_function = text_explanation_prediction_wrapper(
            model.prediction_function, input_df, text_column
        )
        text_explainer.fit(text_document, prediction_function)
        html_response = text_explainer.show_prediction(target_names=model.classification_labels)._repr_html_()
        return ExplainTextResponse(explanations=parse_text_explainer_response(html_response))

    def runModelForDataFrame(self, request: RunModelForDataFrameRequest, context):
        model = deserialize_model(request.model)
        df = pd.DataFrame([r.columns for r in request.dataframe.rows])
        predictions = model.run_predict(df)
        if model.model_type == "classification":
            return RunModelForDataFrameResponse(all_predictions=self.pandas_df_to_proto_df(predictions.all_predictions),
                                                prediction=predictions.prediction.astype(str))
        else:
            return RunModelForDataFrameResponse(prediction=predictions.prediction.astype(str),
                                                raw_prediction=predictions.prediction)

    def runModel(self, request: RunModelRequest, context) -> RunModelResponse:
        import numpy as np
        model = deserialize_model(request.model)
        dataset = deserialize_dataset(request.dataset)
        prediction_results = model.run_predict(dataset.df)

        if model.model_type == "classification":
            results = prediction_results.all_predictions
            labels = {k: v for k, v in enumerate(model.classification_labels)}
            assert dataset.target in dataset.df, f"Target column '{dataset.target}' is not present in the dataset"
            label_serie = dataset.df[dataset.target]
            if len(model.classification_labels) > 2 or model.classification_threshold is None:
                preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
                sorted_predictions = np.sort(prediction_results.all_predictions.values)
                abs_diff = pd.Series(sorted_predictions[:, -1] - sorted_predictions[:, -2], name="absDiff")
            else:
                diff = prediction_results.all_predictions.iloc[:, 1] - model.classification_threshold
                preds_serie = (diff >= 0).astype(int).map(labels).rename("predictions")
                abs_diff = pd.Series(diff.abs(), name="absDiff")
            calculated = pd.concat([preds_serie, label_serie, abs_diff], axis=1)
        else:
            results = pd.Series(prediction_results.prediction)
            preds_serie = results
            target_serie = dataset.df[dataset.target]
            diff = preds_serie - target_serie
            diff_percent = pd.Series(diff / target_serie, name="diffPercent")
            abs_diff = pd.Series(diff.abs(), name="absDiff")
            abs_diff_percent = pd.Series(abs_diff / target_serie, name="absDiffPercent")
            calculated = pd.concat([preds_serie, target_serie, abs_diff, abs_diff_percent, diff_percent], axis=1)

        return RunModelResponse(
            results_csv=results.to_csv(index=False),
            calculated_csv=calculated.to_csv(index=False)
        )

    @staticmethod
    def pandas_df_to_proto_df(df):
        return DataFrame(
            rows=[DataRow(columns=r.astype(str).to_dict()) for _, r in df.iterrows()])

    @staticmethod
    def pandas_series_to_proto_series(self, series):
        return
