from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model that uses email as the primary login identifier.
    Extends Django's AbstractUser with additional profile fields.
    """

    username = None
    objects = UserManager()
    email = models.EmailField(unique=True, verbose_name="email address")
    # first_name and last_name inherited from AbstractUser (max_length=150, blank=True)
    street_address = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=2, blank=True, default="")
    zip_code = models.CharField(max_length=10, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    insurance_provider = models.CharField(max_length=255, blank=True, default="")
    plan_type = models.CharField(max_length=255, blank=True, default="")
    language_pref = models.CharField(max_length=10, default="en")
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email
