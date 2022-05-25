from pydantic import BaseSettings


class Settings(BaseSettings):
    port: int = 50051
    host: str = '0.0.0.0'
    max_workers: int = 10

    environment: str = ""

    class Config:
        env_prefix = "GSK_"
