from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager that uses email instead of username"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        # Use email as username
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Add any extra fields if needed
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    oauth_provider = models.CharField(
        max_length=50, blank=True, db_index=True
    )  # OAuth filtering
    oauth_uid = models.CharField(
        max_length=255, blank=True, db_index=True
    )  # OAuth lookups

    # Use email as the unique identifier
    email = models.EmailField(unique=True)

    # Use custom manager
    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["email"]),  # Email lookups
            models.Index(fields=["oauth_provider", "oauth_uid"]),  # OAuth lookups
            models.Index(
                fields=["is_active", "date_joined"]
            ),  # Active users by join date
        ]

    def __str__(self):
        return self.email or self.username
