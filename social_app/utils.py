from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def is_valid_email(email):
    validator = EmailValidator()
    try:
        validator(email)
        return True
    except ValidationError:
        return False
