from typing import Sequence

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.issues import OUTPUT_FORMATTING_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from . import utils
from .business_detector import LLMBusinessDetector

_model_desc_eval_prompt = (
    "Based on the following description, does this AI model require a specific format for its output? Answer Y or N."
)


@detector("llm_output_format", tags=["llm", "generative", "text_generation"])
class LLMOutputFormatDetector(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # Let’s check whether the model description provides information about the output format.
        out = utils.llm(
            [
                {"role": "system", "content": _model_desc_eval_prompt},
                {"role": "user", "content": model.meta.description},
            ],
            temperature=0.1,
            max_tokens=1,
        )
        if out.strip().upper() != "Y":
            logger.warning(
                "Skipping the output format checks because the model description does not specify an output format."
            )
            return []

        # Define which output format the model should use.
        # @TODO

        # Check that the format is respected.
        # @TODO

        # I keep for now the legacy behaviour
        return self._run_category_detections(OUTPUT_FORMATTING_ISSUE, model)
