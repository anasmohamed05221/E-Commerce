from passlib.context import CryptContext
import hashlib

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password: str):
    # Bcrypt has a 72-byte limit, truncate if necessary
    return bcrypt_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str): 
    # Bcrypt has a 72-byte limit, truncate if necessary
    return bcrypt_context.verify(plain_password[:72], hashed_password)


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()