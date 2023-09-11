from typing import List, Sequence

import pandas as pd

from ..decorators import detector
from ..issues import Issue, IssueLevel, IssueGroup
from ..llm.utils import infer_dataset
from ...datasets.base import Dataset
from ...llm.issues import LLM_ISSUE_CATEGORIES, LlmIssueCategory
from ...models.langchain import LangchainModel


def validate_prediction(
    model, issue: LlmIssueCategory, test_cases: List[str], dataset: Dataset, predictions: List[str], threshold: float
):
    from ...llm.utils.validate_test_case import validate_test_case

    issues = list()

    df_with_pred = dataset.df.rename(columns={column: f"prompt_input ({column})" for column in dataset.df.columns})
    df_with_pred["prediction_result"] = predictions

    for test_case in test_cases:
        print(f"Validating test: {test_case}")
        failed = [not passed for passed in validate_test_case(model, test_case, predictions)]
        failed_count = len([result for result in failed if result])
        metric = failed_count / len(predictions)
        print(f"Results: {metric} ({failed_count})")

        if failed_count > 0:
            print("Test failed")

            issues.append(
                Issue(
                    model,
                    dataset,
                    level=IssueLevel.MAJOR if metric < threshold else IssueLevel.MINOR,
                    group=IssueGroup(name=issue.name, description=issue.description),
                    description=f"For the test '{test_case}', we found that {metric * 100:.2f} of the generated answers does not respect it.",
                    # Todo: add more meta
                    meta={"metric": metric, "test_case": test_case},
                    examples=df_with_pred[failed],
                    tests=_generate_business_test,
                )
            )

    return issues


@detector("llm_business", tags=["business", "llm", "generative", "text_generation"])
class LLMBusinessDetector:
    def __init__(self, threshold: float = 0.6, num_samples=10, num_tests=4):
        self.threshold = threshold
        self.num_samples = num_samples
        self.num_tests = num_tests

    def run(self, model: LangchainModel, dataset: Dataset) -> Sequence[Issue]:
        potentially_failing_dataset = dataset = infer_dataset(
            f"""
            Name: {model.meta.name}
            
            Description: {model.meta.description}
            """,
            model.meta.feature_names,
            True,
        )
        print(f"Generated potentially failing prompts: {potentially_failing_dataset}")

        df = pd.concat([potentially_failing_dataset.df, dataset.df]).reset_index(drop=True)
        df = df.head(min(len(df.index), self.num_samples))
        dataset = Dataset(df)

        predictions = model.predict(dataset).prediction

        issues = []

        for issue in LLM_ISSUE_CATEGORIES:
            try:
                test_cases = issue.issue_generator.run_and_parse(
                    model_name=model.meta.name, model_description=model.meta.description
                ).assertions[:3]
                print(f"Generated tests: {test_cases}")

                issues += validate_prediction(model, issue, test_cases, dataset, predictions, self.threshold)
            except Exception as e:
                print(f"Failed to evaluate {issue}: {e}")

        return issues


def _generate_business_test(issue: Issue):
    from ...testing.tests.llm import test_test_case

    # Only generates a single business test
    return {
        issue.meta["test_case"]: test_test_case(
            model=issue.model,
            dataset=issue.dataset,
            test_case=issue.meta["test_case"],
            slicing_function=None,
            threshold=issue.meta["metric"],
        )
    }
