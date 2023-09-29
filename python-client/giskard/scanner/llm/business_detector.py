from typing import List, Sequence

import openai
import pandas as pd

from ...datasets.base import Dataset
from ...llm.issues import LLM_ISSUE_CATEGORIES, LlmIssueCategory
from ...models.base.model import BaseModel
from ...models.langchain import LangchainModel
from ..issues import Issue, IssueGroup, IssueLevel
from ..logger import logger
from ..scanner import maybe_print


def validate_prediction(
    model,
    issue: LlmIssueCategory,
    test_cases: List[str],
    dataset: Dataset,
    predictions: List[str],
    threshold: float,
    verbose=True,
):
    from ...llm.utils.validate_test_case import validate_test_case_with_reason

    issues = list()

    df_with_pred = dataset.df.rename(columns={column: f"prompt_input ({column})" for column in dataset.df.columns})
    df_with_pred["prediction_result"] = predictions

    for test_case in test_cases:
        maybe_print(f"Validating test: {test_case}", verbose=verbose)
        results = pd.DataFrame.from_records(
            [result.__dict__ for result in validate_test_case_with_reason(model, test_case, dataset.df, predictions)]
        )
        failed = results["score"] < 3
        failed_count = len([result for result in failed if result])
        metric = failed_count / len(predictions)
        maybe_print(f"Results: {metric} ({failed_count})", verbose=verbose)

        df_with_pred_and_test_results = pd.concat([df_with_pred, results[["reason", "tip"]]], axis=1)

        if failed_count > 0:
            maybe_print("Test failed", verbose)

            issues.append(
                Issue(
                    model,
                    dataset,
                    level=IssueLevel.MAJOR if metric >= threshold else IssueLevel.MINOR,
                    group=IssueGroup(name=issue.name, description=issue.description),
                    description=f"For the test '{test_case}', we found that {metric * 100:.2f} of the generated answers does not respect it.",
                    meta={
                        "domain": test_case,
                        "metric_value": metric,
                        "test_case": test_case,
                        "deviation": f"{round(metric * 100, 2)}% of generated inputs does not respect the test",
                        "hide_index": True,
                    },
                    examples=df_with_pred_and_test_results[failed],
                    tests=_generate_business_test,
                )
            )

    return issues


class LLMBusinessDetector:
    def __init__(self, threshold: float = 0.6, num_samples=10, num_tests=3):
        self.threshold = threshold
        self.num_samples = num_samples
        self.num_tests = num_tests

    def _llm(self, messages, model="gpt-4", temperature=0.5, **kwargs):
        completion = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, **kwargs)
        return completion.choices[0].message.content

    def run(self, model: LangchainModel, _: Dataset, verbose=True, **kwargs) -> Sequence[Issue]:
        # First, let us rephrase the model description so that it is standardized and clear for our analysis.
        model_desc = self._reformulate_model_description(model)

        logger.debug(f"Reformulated model description: {model_desc}")

        # Decide which issue categories we should use.
        categories = self._select_relevant_categories(model_desc)
        logger.debug(f"Selected issue categories: {[c.name for c in categories]}")

        # We run our detection for each issue category.
        issues = []

        for category in categories:
            issues += self._run_category_detections(category, model)

        return issues

    def _reformulate_model_description(self, model: BaseModel):
        return self._llm(
            [
                {
                    "role": "system",
                    "content": "You are given the description of an AI model. Please reformulate it in English to be a concise but complete description of the model in the context of a technical audit.",
                },
                {"role": "user", "content": model.meta.description},
            ],
            temperature=0.1,
        )

    def _select_relevant_categories(self, model_desc: str):
        # @TODO: improve this
        selection = []
        for category in LLM_ISSUE_CATEGORIES:
            category.description
            out = self._llm(
                [
                    {
                        "role": "system",
                        "content": f"""You are conducting an audit on an AI model on this model: {model_desc}

Define if this category of issues is relevant to the given model: {category.name} - {category.description}.

Answer 'Y' if the issue category is relevant for the audit of the model, 'N' otherwise.""",
                    },
                ],
                temperature=0.1,
                max_tokens=1,
            )

            if out.strip().upper().startswith("Y"):
                selection.append(category)

        return selection

    def _run_category_detections(self, issue_category: LlmIssueCategory, model: BaseModel, use_issue_examples=False):
        verbose = True

        if not use_issue_examples:
            test_cases = (
                issue_category.issue_generator(self.num_tests)
                .run(model_name=model.meta.name, model_description=model.meta.description)
                .assertions[: self.num_tests]
            )
        else:
            test_cases = issue_category.issue_examples

        potentially_failing_inputs = issue_category.input_generator(model.meta.feature_names, self.num_samples).run(
            model_name=model.meta.name,
            model_description=model.meta.description,
            variables=model.meta.feature_names,
            generated_tests=test_cases,
        )["inputs"][: self.num_samples]

        evaluation_dataset = Dataset(
            pd.DataFrame(
                [
                    {key: value for key, value in potentially_failing_input.items() if key in model.meta.feature_names}
                    for potentially_failing_input in potentially_failing_inputs
                ]
            ),
            name=f"{issue_category.name} evaluation dataset generated by scan",
            validation=False,
        )

        maybe_print(f"Generated evaluation dataset for {issue_category.name}: {evaluation_dataset.df}", verbose=verbose)

        predictions = model.predict(evaluation_dataset).prediction

        issues = validate_prediction(
            model, issue_category, test_cases, evaluation_dataset, predictions, self.threshold, verbose
        )

        return issues


def _generate_business_test(issue: Issue):
    from ...testing.tests.llm import test_llm_response_validation

    # Only generates a single business test
    return {
        issue.meta["test_case"]: test_llm_response_validation(
            model=issue.model,
            dataset=issue.dataset,
            evaluation_criteria=issue.meta["test_case"],
            threshold=1 - issue.meta["metric_value"],
        )
    }
