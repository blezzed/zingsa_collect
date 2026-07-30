from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Collect account profile (Kobo-style account metadata)."""

    country = models.CharField(max_length=64, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    sector = models.CharField(max_length=64, blank=True, default="")
    organization_type = models.CharField(max_length=128, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    social_linkedin = models.CharField(max_length=255, blank=True, default="")
    newsletter_opt_in = models.BooleanField(default=False)
