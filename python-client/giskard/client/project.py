from requests_toolbelt.sessions import BaseUrlSession

from giskard.utils.analytics_collector import anonymize, analytics


class Project:
    def __init__(self, session: BaseUrlSession, project_key: str, project_id: int) -> None:
        self.project_key = project_key
        self._session = session
        self.url = self._session.base_url.replace("/api/v2/", "")
        self.project_id = project_id

    def _update_test_suite_params(self, actual_ds_id, reference_ds_id, model_id, test_id=None, test_suite_id=None):
        assert test_id is not None or test_suite_id is not None, "Either test_id or test_suite_id should be specified"
        res = self._session.put(
            "testing/suites/update_params",
            json={
                "testSuiteId": test_suite_id,
                "testId": test_id,
                "referenceDatasetId": reference_ds_id,
                "actualDatasetId": actual_ds_id,
                "modelId": model_id,
            },
        )
        assert res.status_code == 200, "Failed to update test suite"

    def list_tests_in_suite(self, suite_id):
        assert suite_id is not None, "suite_id should be specified"
        res = self._session.get("testing/tests", params={"suiteId": suite_id}).json()
        return [{"id": t["id"], "name": t["name"]} for t in res]

    def list_test_suites(self):
        res = self._session.get(f"testing/suites/{self.project_id}").json()
        return [{"id": t["id"], "name": t["name"]} for t in res]

    def _execution_dto_filter(self, answer_json):
        res = {
            "id": answer_json["testId"],
            "name": answer_json["testName"],
            "status": answer_json["status"],
            "executionDate": answer_json["executionDate"],
            "message": answer_json["message"],
        }
        if answer_json["status"] != "ERROR":
            res["metric"] = answer_json["result"][0]["result"]["metric"]
        return res

    def execute_test(self, test_id, actual_ds_id=None, reference_ds_id=None, model_id=None):
        analytics.track(
            "execute_test",
            {
                "test_id": anonymize(test_id),
                "actual_ds_id": anonymize(actual_ds_id),
                "reference_ds_id": anonymize(reference_ds_id),
                "model_id": anonymize(model_id),
            },
        )
        assert test_id is not None, "test_id should be specified"

        self._update_test_suite_params(actual_ds_id, reference_ds_id, model_id, test_id=test_id)
        answer_json = self._session.post(f"testing/tests/{test_id}/run").json()
        return self._execution_dto_filter(answer_json)

    def execute_test_suite(self, test_suite_id, actual_ds_id=None, reference_ds_id=None, model_id=None):
        analytics.track(
            "execute_test_suite",
            {
                "test_suite_id": anonymize(test_suite_id),
                "actual_ds_id": anonymize(actual_ds_id),
                "reference_ds_id": anonymize(reference_ds_id),
                "model_id": anonymize(model_id),
            },
        )
        assert test_suite_id is not None, "test_suite_id should be specified"
        self._update_test_suite_params(
            actual_ds_id,
            reference_ds_id,
            model_id,
            test_suite_id=test_suite_id,
        )
        answer_json = self._session.post("testing/suites/execute", json={"suiteId": test_suite_id}).json()
        return [self._execution_dto_filter(test) for test in answer_json]

    def __repr__(self) -> str:
        return f"GiskardProject(project_key='{self.project_key}')"
