from typing import Dict

import os
import re
from abc import ABC

import sentry_sdk
from sentry_sdk.integrations.excepthook import ExcepthookIntegration
from sentry_sdk.scrubber import DEFAULT_DENYLIST

WHITELISTED_MODULES = ["giskard", "pandas", "numpy"]
DISABLE_SENTRY_ENV_VARIABLE_NAME = "GSK_DISABLE_SENTRY"


def _lower_text_only_var_name(var_name: str):
    # Remove underscore and digits and put to lower case
    return re.sub(r"[0-9_]+", "", var_name.lower())


SENSITIVE_VAR_NAME = [
    _lower_text_only_var_name(var_name) for var_name in DEFAULT_DENYLIST + ["df", "batch", "requirement"]
]


def _scrub_nonsensitive_frame(frame):
    if "vars" in frame:
        frame["vars"] = {
            var_name: "[Filtered]" if _lower_text_only_var_name(var_name) in SENSITIVE_VAR_NAME else value
            for var_name, value in frame["vars"].items()
        }

    return frame


def _scrub_sensitive_frame(frame):
    if "vars" in frame:
        frame["vars"] = {var_name: "[Filtered]" for var_name in frame["vars"].keys()}

    # Anonymize code
    frame["pre_context"] = ["[filtered_pre_context]"]
    frame["context_line"] = ["[filtered_context_line]"]
    frame["post_context"] = ["[filtered_pre_context]"]

    return frame


def scrub_frame(frame):
    is_nonsensitive = (
        "module" in frame and frame["module"] is not None and frame["module"].split(".")[0] in WHITELISTED_MODULES
    )

    return _scrub_nonsensitive_frame(frame) if is_nonsensitive else _scrub_sensitive_frame(frame)


def scrub_stacktrace(stacktrace):
    if "frames" not in stacktrace:
        return stacktrace

    stacktrace["frames"] = [scrub_frame(frame) for frame in stacktrace["frames"]]

    return stacktrace


def scrub_event(event, _hint) -> Dict[str, ABC]:
    if "exception" not in event:
        return event

    exception = event["exception"]
    if "values" not in exception:
        return event

    for value in exception["values"]:
        if "stacktrace" in value:
            value["stacktrace"] = scrub_stacktrace(value["stacktrace"])

    return event


def configure_sentry():
    if os.getenv(DISABLE_SENTRY_ENV_VARIABLE_NAME, "False").lower() in ("true", "1", "yes", "t", "y"):
        return None

    sentry_sdk.init(
        # DSN is safe to be publicly available: https://docs.sentry.io/product/sentry-basics/concepts/dsn-explainer/
        dsn="https://a5d33bfa91bc3da9af2e7d32e19ff89d@o4505952637943808.ingest.sentry.io/4506789759025152",
        enable_tracing=True,
        integrations=[ExcepthookIntegration(always_run=True)],
        before_send=scrub_event,
    )
