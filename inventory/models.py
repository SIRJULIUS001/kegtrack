from django.db import models
from decimal import Decimal


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )

    class Meta:
        unique_together = ("name", "parent")

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ProductVariant(models.Model):

    VOLUME_CHOICES = [
        ("1L", "1 Litre"),
        ("750ml", "750 ml"),
        ("500ml", "500 ml"),
        ("300ml", "300 ml"),
        ("250ml", "250 ml"),
        ("30ml", "30 ml (Shot)"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    volume = models.CharField(max_length=20, choices=VOLUME_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "volume"],
                name="unique_product_variant"
            )
        ]
        indexes = [
            models.Index(fields=["product"])
        ]
        ordering = ["product", "volume"]

    def __str__(self):
        return f"{self.product.name} - {self.volume}"


class LocationPoint(models.Model):

    TYPE_CHOICES = [
        ("counter", "Counter"),
        ("table", "Table"),
        ("bar", "Bar"),
        ("store", "Store Room"),
    ]

    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="locations"
    )

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["business", "name", "type"],
                condition=models.Q(is_deleted=False),
                name="unique_active_location_per_business"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"

    # =========================
    # BUSINESS ACTION METHODS
    # =========================

    def rename(self, new_name):
        self.name = new_name
        self.save(update_fields=["name"])

    def change_type(self, new_type):
        self.type = new_type
        self.save(update_fields=["type"])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def delete_soft(self):
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])

from django.db import models
from django.db.models import F
from decimal import Decimal


from decimal import Decimal
from django.db import models
from django.db.models import F

class StockAtLocation(models.Model):

    location = models.ForeignKey(
        "inventory.LocationPoint",
        on_delete=models.CASCADE,
        related_name="stock_items"
    )

    variant = models.ForeignKey(
        "inventory.ProductVariant",
        on_delete=models.PROTECT,
        related_name="location_stock"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    reserved_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # ✅ COUNTER PRICE (KEY FIX)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["location", "variant"],
                name="unique_stock_per_location"
            )
        ]
        ordering = ["location", "variant"]

    def __str__(self):
        return f"{self.location} - {self.variant} ({self.quantity})"

    # =========================
    # BUSINESS LOGIC
    # =========================

    def available_stock(self):
        return self.quantity - self.reserved_quantity

    def add_stock(self, amount):
        amount = Decimal(amount)

        StockAtLocation.objects.filter(pk=self.pk).update(
            quantity=F("quantity") + amount
        )
        self.refresh_from_db()

    def deduct_stock(self, amount):
        amount = Decimal(amount)

        if amount > self.available_stock():
            raise ValueError("Not enough stock available")

        StockAtLocation.objects.filter(pk=self.pk).update(
            quantity=F("quantity") - amount
        )
        self.refresh_from_db()
        
        
class StockMovement(models.Model):

    MOVEMENT_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("ADJUST", "Adjustment"),
        ("TRANSFER", "Transfer"),
    ]

    # =========================
    # MULTI-TENANT SAFETY (FIXED)
    # =========================
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="stock_movements"
    )

    variant = models.ForeignKey(
        "inventory.ProductVariant",
        on_delete=models.PROTECT,
        related_name="movements"
    )

    location = models.ForeignKey(
        "inventory.LocationPoint",
        on_delete=models.CASCADE,
        related_name="movements"
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    note = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "location"]),
        ]

    def __str__(self):
        return f"{self.movement_type} | {self.variant} | {self.quantity}"

    # =========================
    # SAFETY CHECK (IMPORTANT)
    # =========================

    def clean(self):
        if self.location.business_id != self.business_id:
            raise ValueError("Location does not belong to this business")

    # =========================
    # HELPERS
    # =========================

    def is_in(self):
        return self.movement_type == "IN"

    def is_out(self):
        return self.movement_type == "OUT"