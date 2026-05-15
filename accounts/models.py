from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# =========================
# ROLE MODEL
# =========================
class Role(models.Model):

    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"

    ROLE_CHOICES = [
        (OWNER, "Business Owner"),
        (MANAGER, "Manager"),
        (STAFF, "Staff"),
    ]

    # 🔥 CORE ROLE CODE (this is what you should always use in logic)
    name = models.CharField(max_length=20, choices=ROLE_CHOICES)

    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # 🔥 RBAC PERMISSIONS
    permissions = models.ManyToManyField(
        "accounts.Permission",
        blank=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # =========================
    # HELPERS (IMPORTANT)
    # =========================
    @property
    def code(self):
        return self.name  # alias for cleaner logic

    def is_owner(self):
        return self.name == self.OWNER

    def is_manager(self):
        return self.name == self.MANAGER

    def is_staff(self):
        return self.name == self.STAFF

    def __str__(self):
        if self.business:
            return f"{self.name} ({self.business.name})"
        return f"{self.name} (TEMPLATE)"
# =========================
# USER MANAGER
# =========================
class UserManager(BaseUserManager):

    def create_user(self, username, email, phone, password=None, **extra_fields):

        if not username:
            raise ValueError("Username is required")

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            phone=phone,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_superadmin", True)
        extra_fields.setdefault("is_active_staff", True)
        extra_fields.setdefault("is_deleted", False)

        return self.create_user(username, email, phone, password, **extra_fields)


# =========================
# USER MODEL
# =========================
class User(AbstractUser):

    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)

    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_superadmin = models.BooleanField(default=False)

    is_active_staff = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_device = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone", "first_name", "last_name"]

    objects = UserManager()

    # =========================
    # LOGIN RULE
    # =========================
    def can_login(self):
        return (
            self.is_active and
            self.is_active_staff and
            not self.is_deleted
        )

    # =========================
    # RBAC ENGINE CORE
    # =========================
    def has_permission(self, code):

        # SUPERADMIN BYPASS
        if self.is_superadmin or self.is_superuser:
            return True

        if not self.role:
            return False

        return self.role.permissions.filter(code=code).exists()

    # =========================
    # HELPERS
    # =========================
    @property
    def role_name(self):
        return self.role.name if self.role else "No Role"

    @property
    def business_name(self):
        return self.business.name if self.business else "Global"


# =========================
# PERMISSION MODEL
# =========================
class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name