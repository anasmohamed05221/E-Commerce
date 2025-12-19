from utils.verification import generate_verification_code, get_code_expiry_time
from datetime import datetime, timedelta, timezone

def test_generate_verification_code():
    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()

def test_code_expiry_time():
    expiry = get_code_expiry_time(minutes=10)
    now = datetime.now(timezone.utc)
    assert expiry > now
    assert expiry < now + timedelta(minutes=11)