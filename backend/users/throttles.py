from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """5 login attempts per 15 minutes per IP address."""

    scope = "login"

    def __init__(self):
        super().__init__()
        # DRF parses "5/hour" from settings (num_requests=5, duration=3600).
        # Override duration to 15 minutes (900s) while keeping num_requests=5.
        self.num_requests = 5
        self.duration = 900


class RegisterRateThrottle(AnonRateThrottle):
    """5 registration attempts per hour per IP address."""

    scope = "register"


class PasswordResetThrottle(AnonRateThrottle):
    """5 password reset requests per hour per IP address."""

    scope = "password_reset"
