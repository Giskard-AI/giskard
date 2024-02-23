import sentry_sdk
from sentry_sdk.integrations.excepthook import ExcepthookIntegration
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

from giskard.utils.analytics_collector import anonymize

denylist = DEFAULT_DENYLIST + ["AZURE_OPENAI_API_KEY", "OPENAI_API_KEY", "GSK_API_KEY"]
WHITELISTED_MODULES = ["giskard"]


def _anonymize_value(data, key, prefix="", suffix=""):
    if key in data:
        data[key] = prefix + anonymize(data[key]) + suffix


def _replace_value(data, key, replacement):
    if key in data:
        data[key] = replacement


def _anonymize_stacktrace(stacktrace):
    if "frames" not in stacktrace:
        return

    for frame in stacktrace["frames"]:
        if "module" in frame and frame["module"] is not None and frame["module"].split(".")[0] in WHITELISTED_MODULES:
            continue

        _anonymize_value(frame, "filename", suffix=".py")
        _anonymize_value(frame, "abs_path", prefix="/anonymized/path/", suffix=".py")
        _anonymize_value(frame, "module", prefix="anonymized.module.")
        _replace_value(frame, "pre_context", ["pre_context=anonymized"])
        _anonymize_value(frame, "context_line")
        _replace_value(frame, "post_context", ["post_context=anonymized"])
        _replace_value(frame, "vars", {"vars": "anonymized"})


def _strip_sensitive_module(event):
    print("_____ EVENT ______")

    # If execution info are available, only keep information from whitelisted modules
    if "exception" not in event:
        return event

    exception = event["exception"]
    if "values" not in exception:
        return event

    for value in exception["values"]:
        if "stacktrace" in value:
            _anonymize_stacktrace(value["stacktrace"])

    return event


def strip_sensitive_data(event, hint):
    return _strip_sensitive_module(event)


def configure_sentry():
    sentry_sdk.init(
        dsn="https://a5d33bfa91bc3da9af2e7d32e19ff89d@o4505952637943808.ingest.sentry.io/4506789759025152",
        enable_tracing=True,
        integrations=[ExcepthookIntegration(always_run=True)],
        event_scrubber=EventScrubber(denylist=denylist),
        before_send=strip_sensitive_data,
    )
