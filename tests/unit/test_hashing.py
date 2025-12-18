from utils.hashing import verify_password, get_password_hash

def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    assert hashed != password

    empty_pass = ""
    hashed_empty = get_password_hash(empty_pass)
    assert empty_pass != hashed_empty


    

def test_password_verification():
    password = "supersecretpassword"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

    long_pass = "a" * 100
    hashed_long = get_password_hash(long_pass)
    assert verify_password(long_pass, hashed_long) is True

    empty_pass = ""
    hashed_empty = get_password_hash(empty_pass)
    assert verify_password(empty_pass, hashed_empty) is True