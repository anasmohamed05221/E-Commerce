from pydantic import BaseModel, EmailStr, field_validator
import phonenumbers
import re

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: str 
    last_name: str
    password: str 
    phone_number: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        """
        Password must be at least 8 characters and contain:
        - At least one letter
        - At least one digit
        """
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')

        if not re.search(r'[A-Za-z]', value):
            raise ValueError('Password must contain at least one letter')


        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit')

        return value

    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, value):
        """
        Validates phone number format using Google's phonenumbers library.
        Accepts international format: +201234567890
        """
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError('Invalid phone number')

            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        except phonenumbers.NumberParseException:
            raise ValueError('Phone number must include country code (e.g.: +966xxxxxxxxx, +20xxxxxxxxxx)')


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator('code')
    @classmethod
    def validate_code(cls, value):
        if len(value)!=6:
            raise ValueError('must be a 6-digit code')
        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    @field_validator('refresh_token')
    @classmethod
    def validate_token(cls, value):
        if not value or not value.strip():
            raise ValueError('Refresh token cannot be empty')
        return value

class RevokeTokenRequest(BaseModel):
    refresh_token: str

    @field_validator('refresh_token')
    @classmethod
    def validate_token(cls, value):
        if not value or not value.strip():
            raise ValueError('Refresh token cannot be empty')
        return value

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, value):
        """
        Password must be at least 8 characters and contain:
        - At least one letter
        - At least one digit
        """
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')

        if not re.search(r'[A-Za-z]', value):
            raise ValueError('Password must contain at least one letter')


        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit')

        return value


class ForgotPasswordRequest(BaseModel):
    email: EmailStr



class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, value):
        """
        Password must be at least 8 characters and contain:
        - At least one letter
        - At least one digit
        """
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')

        if not re.search(r'[A-Za-z]', value):
            raise ValueError('Password must contain at least one letter')


        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit')

        return value
