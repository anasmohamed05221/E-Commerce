import random
from datetime import datetime, timezone, timedelta

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))

def get_code_expiry_time(minutes: int=10) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)