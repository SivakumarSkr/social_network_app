from typing import Optional
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def is_valid_email(email: Optional[str]) -> bool:
    validator: EmailValidator = EmailValidator()
    try:
        validator(email)
        return True
    except ValidationError:
        return False
