from typing import Dict, Any

from tests.utils import MockedClient, match_model_id
import pytest
from giskard.testing import test_f1
from giskard.ml_worker.server.ml_worker_service import MLWorkerServiceImpl


@pytest.mark.parametrize("data,model,", [("german_credit_data", "german_credit_model")])
def test_service(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    with MockedClient() as (client, mr):
        project_key = "test_project"
        saved_id_model = model.upload(client, project_key)
        saved_id_data = data.upload(client, project_key)
        match_model_id(saved_id_model)
        match_model_id(saved_id_data)

        # Check the case where the test fails and the debug returns a dataset
        arguments: dict[str, Any] = {"model": model, "dataset": data, "threshold": 0.9, "debug": True}
        debug_info = {"project_key": project_key,
                      "suffix": "Debug: test_f1 | <model:" + saved_id_model + "> | <dataset:" + saved_id_data + ">"}

        result = MLWorkerServiceImpl.do_run_adhoc_test(client, arguments, test_f1, debug_info)
        match_model_id(result.output_df_id)

        # Check the case where the test does not fail but the backend is requesting to debug
        arguments: dict[str, Any] = {"model": model, "dataset": data, "threshold": 0.1, "debug": True}
        debug_info = {"project_key": project_key,
                      "suffix": "Debug: test_f1 | <model:" + saved_id_model + "> | <dataset:" + saved_id_data + ">"}

        with pytest.raises(
                ValueError,
                match=r"You have requested to debug the test, but the test did not return a debuggable output.",
        ):
            MLWorkerServiceImpl.do_run_adhoc_test(client, arguments, test_f1, debug_info)

        # Check the case where the test fails but the debug_info is None
        arguments: dict[str, Any] = {"model": model, "dataset": data, "threshold": 0.9, "debug": True}
        debug_info = None

        with pytest.raises(
                ValueError,
                match="You have requested to debug the test, "
                      "but extract_debug_info did not return the information needed.",
        ):
            MLWorkerServiceImpl.do_run_adhoc_test(client, arguments, test_f1, debug_info)
