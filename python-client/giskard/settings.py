import os
from pathlib import Path
from typing import Optional

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
    port: int = 50051
    host: str = "localhost"
    max_workers: int = 10
    max_send_message_length_mb: int = 1024
    max_receive_message_length_mb: int = 1024
    loglevel = "INFO"

    class Config:
        env_prefix = "GSK_"

    @property
    def home_dir(self) -> Path:
        return Path(expand_env_var(self.home))


settings = Settings()
