from typing import Dict, Optional, Sequence, Tuple

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ...core.test_result import TestResultDetails, TestResultStatus
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..client import LLMClient, get_default_client
from ..client.base import ChatMessage
from ..errors import LLMGenerationError
from .utils import format_conversation

logger = logging.getLogger("giskard.llm")


@dataclass
class EvaluationResultExample:
    # The status of the example
    status: TestResultStatus
    sample: Optional[Sequence[Dict]]
    # The reason why the example have given status
    reason: Optional[str]

    @property
    def to_example(self):
        if self.status == TestResultStatus.ERROR:
            return {"error": self.reason, "sample": self.sample}
        else:
            return {"reason": self.reason, "sample": self.sample}


@dataclass
class EvaluationResult:
    results: Sequence[EvaluationResultExample] = field(default_factory=list)

    @property
    def failure_examples(self):
        return [failed.to_example for failed in self.results if failed.status == TestResultStatus.FAILED]

    @property
    def success_examples(self):
        return [passed.to_example for passed in self.results if passed.status == TestResultStatus.PASSED]

    @property
    def errors(self):
        return [error.to_example for error in self.results if error.status == TestResultStatus.ERROR]

    @property
    def passed(self):
        return len(self.failure_examples) == 0 and len(self.success_examples) > 0

    @property
    def failed(self):
        return not self.passed

    @property
    def has_errors(self):
        return len(self.errors) > 0

    @property
    def passed_ratio(self):
        return len(self.success_examples) / (len(self.success_examples) + len(self.failure_examples))

    def add_error(self, error: str, sample: Dict):
        self.results.append(EvaluationResultExample(reason=error, sample=sample, status=TestResultStatus.ERROR))

    def add_sample(self, eval_passed: bool, reason: Optional[str] = None, sample: Optional[Dict] = None):
        status = TestResultStatus.PASSED if eval_passed else TestResultStatus.FAILED
        self.results.append(EvaluationResultExample(reason=reason, sample=sample, status=status))

    @property
    def details(self):
        details = TestResultDetails.empty()

        for result in self.results:
            details.append(
                result.status,
                result.sample.get(["inputs"], {}),
                str(result.sample.get(["conversation"], "No conversation provided")),
                result.sample.get("meta", None),
            )

        return details


class BaseEvaluator(ABC):
    """Base interface for evaluators."""

    @abstractmethod
    def evaluate(self, model: BaseModel, dataset: Dataset):
        ...


class _BaseLLMEvaluator(BaseEvaluator):
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        llm_temperature: float = 0.1,
        llm_seed: int = 42,
        llm_output_format="json",
    ):
        self.llm_client = llm_client if llm_client is not None else get_default_client()
        self.llm_temperature = llm_temperature
        self.llm_seed = llm_seed
        self.llm_output_format = llm_output_format

    @abstractmethod
    def _format_messages(
        self, model: BaseModel, conversation: Sequence[Dict], meta: Optional[Dict] = None
    ) -> Sequence[ChatMessage]:
        ...

    def evaluate(self, model: BaseModel, dataset: Dataset):
        model_outputs = model.predict(dataset).prediction

        result = EvaluationResult()
        for (row_id, row), model_output in zip(
            dataset.df.iterrows(),
            model_outputs,
        ):
            input_vars = {k: v for k, v in row.items() if k in model.feature_names}
            if len(input_vars) == 1:
                input_vars = list(input_vars.values())[0]
            input_meta = {k: v for k, v in row.items() if k not in model.feature_names}
            input_meta["__sample_id"] = row_id

            conversation = [{"role": "user", "content": input_vars}, {"role": "agent", "content": model_output}]
            sample = {
                "inputs": input_vars,
                "conversation": conversation,
                "meta": input_meta,
            }
            logger.debug(f"{self.__class__.__name__}: evaluating sample {sample}")

            messages = self._format_messages(model, conversation, meta=input_meta)
            try:
                raw_eval = self.llm_client.complete(
                    messages,
                    temperature=self.llm_temperature,
                    caller_id=self.__class__.__name__,
                    seed=self.llm_seed,
                    format=self.llm_output_format,
                )
                eval_passed, reason = self._parse_evaluation_output(raw_eval)
                logger.debug(f"{self.__class__.__name__} evaluation result: eval_passed={eval_passed}, reason={reason}")
            except LLMGenerationError as err:
                logger.debug(f"{self.__class__.__name__} evaluation error: {err}")
                result.add_error(str(err), sample)
                continue

            result.add_sample(eval_passed, reason, sample)

        return result

    def _parse_evaluation_output(self, raw_eval: ChatMessage) -> Tuple[bool, str]:
        try:
            eval_result = json.loads(raw_eval.content)
            return eval_result["eval_passed"], eval_result.get("reason")
        except (AttributeError, KeyError, json.JSONDecodeError) as err:
            raise LLMGenerationError("Could not parse evaluator output") from err


class LLMBasedEvaluator(_BaseLLMEvaluator):
    def __init__(
        self,
        prompt: str,
        prefix_messages: Optional[Sequence[ChatMessage]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.prompt = prompt
        self.prefix_messages = prefix_messages or []

    def _format_messages(
        self, model: BaseModel, conversation: Sequence[Dict], meta: Optional[Dict] = None
    ) -> Sequence[ChatMessage]:
        prompt = self.prompt.format(model=model, conversation=format_conversation(conversation))
        return self.prefix_messages + [ChatMessage(role="user", content=prompt)]
