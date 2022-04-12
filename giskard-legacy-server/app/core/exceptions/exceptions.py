from fastapi import HTTPException
from starlette import status


class ConfigurationException(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'License error: {reason}'
        )
