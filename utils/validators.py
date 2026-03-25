import re
import phonenumbers
def validate_password(value):
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

def validate_phone(value):
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