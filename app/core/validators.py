from django.contrib.auth.password_validation import validate_password


class PasswordValidator:
    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __call__(self, value):
        validate_password(value)
