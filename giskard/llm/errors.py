from ..core.errors import GiskardInstallationError


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"


class LLMGenerationError(RuntimeError):
    """Indicates a failure in LLM-based generation"""
