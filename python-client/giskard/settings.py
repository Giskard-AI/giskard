import os
from pathlib import Path
from typing import Optional
from packaging import version

import pydantic
# See https://linear.app/giskard/issue/GSK-1745/upgrade-pydantic-to-20
IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")

if IS_PYDANTIC_V2:
    # Package have been moved out in Pydantic v2
    from pydantic_settings import BaseSettings
else:
    from pydantic.env_settings import BaseSettings


def expand_env_var(env_var: Optional[str]) -> Optional[str]:
    if not env_var:
        return env_var
    while True:
        interpolated = os.path.expanduser(os.path.expandvars(str(env_var)))
        if interpolated == env_var:
            return interpolated
        else:
            env_var = interpolated


class Settings(BaseSettings):
    home: str = "~/giskard-home"
    ws_port: int = 9000
    ws_path: str = "/ml-worker"
    host: str = "localhost"
    max_workers: int = 10
    max_send_message_length_mb: int = 1024
    max_receive_message_length_mb: int = 1024
    loglevel: str = "INFO"
    cache_dir: str = "cache"
    disable_analytics: bool = False

    class Config:
        env_prefix = "GSK_"

    @property
    def home_dir(self) -> Path:
        return Path(expand_env_var(self.home))


settings = Settings()
