from passlib.context import CryptContext
import hashlib

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password: str):
    return bcrypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return bcrypt_context.verify(plain_password, hashed_password)


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()