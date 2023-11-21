import logging
import os
from enum import Enum
from typing import Optional


class ApiType(Enum):
    openai = (0,)
    azure = 1


def autodetect_client():
    if "GISKARD_SCAN_LLM_API" in os.environ:
        try:
            return ApiType[os.environ["GISKARD_SCAN_API"].lower()]
        except KeyError:
            raise ValueError(
                f"Environment variable GISKARD_SCAN_LLM_API value is not allowed! Allowed values are: {', '.join([api.name for api in ApiType])}"
            )

    if "AZURE_OPENAI_API_KEY" in os.environ:
        return ApiType.azure

    return ApiType.openai


def get_scan_model(api_type: ApiType) -> Optional[str]:
    scan_model = os.environ.get("GISKARD_SCAN_LLM_MODEL")

    if api_type is ApiType.azure and "GISKARD_SCAN_LLM_MODEL" == None:
        raise ValueError("Please provide your LLM model using GISKARD_SCAN_LLM_MODEL environment variable")

    if scan_model is not None:
        logging.warning(
            "You are using a custom model to perform the scan, keep in mind that the results might be affected"
        )

    return scan_model
