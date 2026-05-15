from django.db import models, IntegrityError
from django.utils.text import slugify
from django.utils import timezone


class Business(models.Model):

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    business_type = models.CharField(
        max_length=50,
        choices=[
            ("pub", "Pub"),
            ("bar", "Bar"),
            ("restaurant", "Restaurant"),
            ("club", "Club"),
        ],
        default="pub"
    )

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()

    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#0056b3")

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_businesses"
    )

    is_active = models.BooleanField(default=True)

    # ✅ NEW (soft delete)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while True:
                try:
                    self.slug = slug
                    super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    slug = f"{base_slug}-{counter}"
                    counter += 1
        else:
            super().save(*args, **kwargs)

    # ======================
    # RELATION HELPERS (FIXED)
    # ======================

    def get_active_staff(self):
        return self.staff_members.filter(is_active=True, is_deleted=False)

    def get_owners(self):
        return self.staff_members.filter(
            role__code="owner",
            is_active=True,
            is_deleted=False
        )

    def get_managers(self):
        return self.staff_members.filter(
            role__code="manager",
            is_active=True,
            is_deleted=False
        )

    def get_active_users(self):
        from accounts.models import User
        return User.objects.filter(
            business_memberships__business=self,
            business_memberships__is_active=True,
            business_memberships__is_deleted=False
        )

    # ✅ Soft delete method
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def __str__(self):
        return self.name
    
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

##not used anywhere in the sytem 
class BusinessProductPrice(models.Model):

    CURRENCY_CHOICES = [
        ("KES", "Kenyan Shilling"),
        ("USD", "US Dollar"),
    ]

    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="product_prices"
    )

    variant = models.ForeignKey(
        "inventory.ProductVariant",
        on_delete=models.CASCADE,
        related_name="business_prices"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default="KES"
    )

    is_active = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("business", "variant")
        ordering = ["business", "variant"]
        indexes = [
            models.Index(fields=["business", "variant"]),
        ]

    # =========================
    # CLEAN (SAFE MODE)
    # =========================
    def clean(self):
        """
        OPTIONAL validation only.
        Does NOT break POS flow.
        """

        if not self.business_id or not self.variant_id:
            return

        # Soft validation (no system crash)
        if self.price is None:
            raise ValidationError("Price cannot be empty")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.business.name} - {self.variant} ({self.price})"
    
    
class BusinessStaff(models.Model):
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="staff_members"
    )

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="business_memberships"
    )

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.PROTECT,
        related_name="business_staff_roles"
    )

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    invited_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_invited"
    )

    class Meta:
        unique_together = ("business", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.business} ({self.role})"

    def activate(self):
        self.is_active = True
        self.is_deleted = False
        self.save(update_fields=["is_active", "is_deleted"])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])
        
