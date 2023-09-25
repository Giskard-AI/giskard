from ...core.errors import GiskardInstallationError


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"
