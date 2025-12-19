from utils.logger import sanitize_log_data

def test_password_redaction():
    data = {"email": "user@example.com", "password": "supersecret123"}
    sanitized = sanitize_log_data(data)
    
    assert sanitized["email"] == "user@example.com" 
    assert sanitized["password"] == "***REDACTED***"


def test_token_partial_redaction():
    data = {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.long_token_here"}
    sanitized = sanitize_log_data(data)

    assert len(sanitized["access_token"]) == 11
    assert sanitized["access_token"].startswith(data["access_token"][:8])
    assert sanitized["access_token"].endswith("...")
    assert "long_token_here" not in sanitized["access_token"]


def test_nested_dict_sanitization():
    data = {
        "user": {
            "email": "user@example.com",
            "password": "secret123"
        }
    }
    sanitized = sanitize_log_data(data)

    assert sanitized["user"]["email"] == data["user"]["email"]
    assert sanitized["user"]["password"] == "***REDACTED***"


def test_non_sensitive_data_unchanged():
    data = {"user_id": 123, "email": "test@example.com", "role": "admin"}
    sanitized = sanitize_log_data(data)
    
    assert sanitized == data