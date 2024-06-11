from typing import Optional

import os
from pathlib import Path

import pydantic
from packaging import version
from pydantic import BaseModel

# See https://linear.app/giskard/issue/GSK-1745/upgrade-pydantic-to-20
IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")

if IS_PYDANTIC_V2:
    FIELD_ATTR = "model_fields"
else:
    FIELD_ATTR = "__fields__"


def expand_env_var(env_var: Optional[str]) -> Optional[str]:
    current = env_var
    previous = None
    while current != previous:
        previous = current
        current = os.path.expandvars(current)
    return current


class Settings(BaseModel):
    home: str = "~/giskard-home"
    ws_port: int = 9000
    ws_path: str = "/websocket"
    host: str = "localhost"
    max_workers: int = 10
    loglevel: str = "INFO"
    cache_dir: str = "cache"
    disable_analytics: bool = False
    force_asyncio_event_loop: bool = False
    min_workers: int = 2
    use_pool: bool = True  # For testing/debugging only, do not disable

    class Config:
        env_prefix = "GSK_"

    @property
    def home_dir(self) -> Path:
        return Path(expand_env_var(self.home)).expanduser().resolve()

    @classmethod
    def build_from_env(cls) -> "Settings":
        return Settings(
            **{k: os.getenv(cls.Config.env_prefix + k.upper(), v.default) for k, v in getattr(cls, FIELD_ATTR).items()}
        )


settings = Settings.build_from_env()
