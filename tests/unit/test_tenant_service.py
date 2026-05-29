from services.tenants import TenantService


def test_generate_api_key_format():
    """Returned plaintext must start with vnx_, hash must be 64-char hex, and not equal plaintext."""
    plaintext, hash_ = TenantService._generate_api_key()
    assert plaintext.startswith("vnx_")
    assert len(hash_) == 64
    assert all(c in "0123456789abcdef" for c in hash_)
    assert hash_ != plaintext


def test_generate_api_key_uniqueness():
    """Two consecutive calls must produce different plaintexts and different hashes."""
    plaintext1, hash1 = TenantService._generate_api_key()
    plaintext2, hash2 = TenantService._generate_api_key()
    assert plaintext1 != plaintext2
    assert hash1 != hash2
