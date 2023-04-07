import logging

from giskard.ml_worker.testing.registry.registry import giskard_registry, load_plugins

logger = logging.getLogger(__name__)

load_plugins()
print("\n".join(giskard_registry.get_all().keys()))
