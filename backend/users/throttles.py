from rest_framework.throttling import AnonRateThrottle


class RegisterRateThrottle(AnonRateThrottle):
    """5 registration attempts per hour per IP address."""

    scope = "register"


class PasswordResetThrottle(AnonRateThrottle):
    """5 password reset requests per hour per IP address."""

    scope = "password_reset"
