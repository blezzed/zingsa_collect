from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("staff_role", User.StaffRole.DEVELOPER)
        extra_fields.setdefault("is_staff", True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Collect account profile (Kobo-style account metadata)."""

    class StaffRole(models.IntegerChoices):
        SUPPORT = 1, "Support"
        OPS = 2, "Ops"
        MANAGER = 3, "Manager"
        ADMIN = 4, "Admin"
        DEVELOPER = 5, "Developer"

    objects = UserManager()

    country = models.CharField(max_length=64, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    sector = models.CharField(max_length=64, blank=True, default="")
    organization_type = models.CharField(max_length=128, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    social_linkedin = models.CharField(max_length=255, blank=True, default="")
    newsletter_opt_in = models.BooleanField(default=False)
    staff_role = models.PositiveSmallIntegerField(
        choices=StaffRole.choices,
        null=True,
        blank=True,
        help_text="Platform staff grade. Null = normal Collect end-user.",
    )

    def effective_staff_role(self):
        """Superusers are treated as Developer for capability checks."""
        if self.is_superuser:
            return self.StaffRole.DEVELOPER
        return self.staff_role

    def is_platform_staff(self) -> bool:
        return self.effective_staff_role() is not None

    def is_developer(self) -> bool:
        return self.effective_staff_role() == self.StaffRole.DEVELOPER

    def _role_at_least(self, minimum: int) -> bool:
        role = self.effective_staff_role()
        if role is None:
            return False
        return int(role) >= int(minimum)

    def can_manage_staff(self) -> bool:
        return self.is_developer() or self._role_at_least(self.StaffRole.ADMIN)

    def can_manage_users(self) -> bool:
        return self.is_developer() or self._role_at_least(self.StaffRole.MANAGER)

    def can_view_system_overview(self) -> bool:
        return self.is_developer() or self._role_at_least(self.StaffRole.OPS)

    def can_view_all_feedback(self) -> bool:
        return self.is_developer() or self._role_at_least(self.StaffRole.SUPPORT)

    def can_view_storage(self) -> bool:
        return self.can_view_system_overview()

    def staff_capabilities(self) -> dict:
        return {
            "is_platform_staff": self.is_platform_staff(),
            "is_developer": self.is_developer(),
            "can_manage_staff": self.can_manage_staff(),
            "can_manage_users": self.can_manage_users(),
            "can_view_system_overview": self.can_view_system_overview(),
            "can_view_all_feedback": self.can_view_all_feedback(),
            "can_view_storage": self.can_view_storage(),
        }
