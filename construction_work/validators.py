from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


class AmsterdamEmailValidator(EmailValidator):
    """Amsterdam email validator"""

    def __call__(self, value):
        """Custom email validator"""

        super().__call__(value)
        if not value.endswith("@amsterdam.nl"):
            raise ValidationError(
                "Email must belong to 'amsterdam.nl'", code="invalid_email"
            )
