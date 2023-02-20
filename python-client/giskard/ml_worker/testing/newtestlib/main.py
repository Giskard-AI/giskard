import logging

from giskard.ml_worker.testing.registry.registry import tests_registry, load_plugins

logger = logging.getLogger(__name__)

load_plugins()
print("\n".join(tests_registry.get_all().keys()))
