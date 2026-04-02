from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that uses email as the primary login identifier.
    Extends Django's AbstractUser with additional profile fields.
    """

    username = None  # Remove username field
    email = models.EmailField(unique=True, verbose_name="email address")
    zip_code = models.CharField(max_length=10, blank=True, default="")
    insurance_provider = models.CharField(max_length=255, blank=True, default="")
    plan_type = models.CharField(max_length=255, blank=True, default="")
    language_pref = models.CharField(max_length=10, default="en")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email
