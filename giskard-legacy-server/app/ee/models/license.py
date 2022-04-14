from typing import Optional, List, Any, Dict

from fastapi import HTTPException
from pydantic.main import BaseModel

from app.ee.models.constants import AvailableFeatures
from starlette import status


class LicenseError(HTTPException):

    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'License error: {reason}'
        )


class Plan(BaseModel):
    display_name: str
    code: str
    max_users: Optional[int]
    features: List[AvailableFeatures]

    def is_user_number_beyond_limit(self, user_number):
        return self.max_users is not None and user_number > self.max_users


BASIC = Plan(
    display_name='Basic Plan',
    code='basic',
    max_users=2,
    features=[]
)

ENTERPRISE = Plan(
    display_name='Enterprise Plan',
    code='enterprise',
    max_users=None,
    features=[]
)

ALL_PLANS = [BASIC, ENTERPRISE]
PLANS_BY_CODE = {p.code: p for p in ALL_PLANS}
