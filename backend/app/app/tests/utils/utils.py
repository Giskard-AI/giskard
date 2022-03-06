import random
import string

from app.core.base_model import CaseInsensitiveEmailStr


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> CaseInsensitiveEmailStr:
    return CaseInsensitiveEmailStr(f"{random_lower_string()}@{random_lower_string()}.com")
