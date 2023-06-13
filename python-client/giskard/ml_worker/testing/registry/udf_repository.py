import logging
import os
from dataclasses import dataclass
from pathlib import Path

from git import Repo

from giskard.settings import expand_env_var, settings

logger = logging.getLogger(__name__)
udf_root = Path(expand_env_var(settings.home)) / "cache" / "udf"


@dataclass
class GitConfig:
    repo: str
    user: str
    pwd: str


def load_config() -> GitConfig:
    return GitConfig(
        repo=os.getenv("GIT_REPOSITORY"),
        user=os.getenv("GIT_USER"),
        pwd=os.getenv("GIT_PASSWORD"),
    )


def init_udf_repository(udf_enabled: bool = False) -> bool:
    # Experimental feature, disabled by default
    if not udf_enabled:
        return False

    try:
        config = load_config()

        if config.repo is None:
            logger.warning(
                "UDF repository is not available because the 'GIT_REPOSITORY' environment variable is not set"
            )
            return False

        if udf_root.exists():
            update_udf_repository()
        else:
            clone_udf_repository(config)
    except Exception as e:
        logger.exception("Failed to initialize UDF repo", e)
        return False
    return True


def update_udf_repository():
    repo = Repo(udf_root)

    logger.info("Repository already existing, fetching updates")
    origin = repo.remotes.origin
    origin.pull()

    repo.close()


def clone_udf_repository(config: GitConfig):
    logger.info(f"cloning repository: {config.repo}")

    host = config.repo

    protocol = "http"
    if not host.startswith("http://"):
        protocol = "https"

    host = f"{protocol}://{config.user}:{config.pwd}@{config.repo.replace('http://', '').replace('https://', '')}"

    repo = Repo.clone_from(host, udf_root)
    repo.close()


udf_repo_available = init_udf_repository()
