from decimal import Decimal
from django.db import transaction

from inventory.models import (
    StockMovement,
    StockAtLocation,
    ProductVariant,
    LocationPoint
)


class StockEngine:

    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"

    MOVEMENT_TYPES = {IN, OUT, ADJUST}

    # =========================
    # CORE ENGINE
    # =========================
    @staticmethod
    @transaction.atomic
    def create_movement(
        *,
        variant: ProductVariant,
        location: LocationPoint,
        movement_type: str,
        quantity,
        user=None,
        reference: str = "",
        note: str = ""
    ):
        if movement_type not in StockEngine.MOVEMENT_TYPES:
            raise ValueError("Invalid movement type")

        quantity = Decimal(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        # ✅ SAFE TENANT VALIDATION
        is_valid = variant.product.business_links.filter(
            business=location.business,
            is_active=True
        ).exists()

        if not is_valid:
            # Do not crash system
            return None

        movement = StockMovement.objects.create(
            variant=variant,
            location=location,
            movement_type=movement_type,
            quantity=quantity,
            created_by=user,
            reference=reference,
            note=note
        )

        StockEngine._apply_to_cache(movement)
        return movement

    # =========================
    # CACHE UPDATE
    # =========================
    @staticmethod
    def _apply_to_cache(movement):
        stock, _ = StockAtLocation.objects.get_or_create(
            location=movement.location,
            variant=movement.variant,
            defaults={"quantity": Decimal("0")}
        )

        qty = Decimal(movement.quantity)

        if movement.movement_type == StockEngine.IN:
            stock.quantity += qty

        elif movement.movement_type == StockEngine.OUT:
            if stock.quantity < qty:
                raise ValueError("Stock cannot go negative")
            stock.quantity -= qty

        elif movement.movement_type == StockEngine.ADJUST:
            stock.quantity = qty

        stock.save()

    # =========================
    # PUBLIC METHODS
    # =========================
    @staticmethod
    def add_stock(*, variant, location, quantity, user=None, reference=""):
        return StockEngine.create_movement(
            variant=variant,
            location=location,
            movement_type=StockEngine.IN,
            quantity=quantity,
            user=user,
            reference=reference
        )

    @staticmethod
    def remove_stock(*, variant, location, quantity, user=None, reference=""):
        return StockEngine.create_movement(
            variant=variant,
            location=location,
            movement_type=StockEngine.OUT,
            quantity=quantity,
            user=user,
            reference=reference
        )

    @staticmethod
    def adjust_stock(*, variant, location, quantity, user=None, reference=""):
        return StockEngine.create_movement(
            variant=variant,
            location=location,
            movement_type=StockEngine.ADJUST,
            quantity=quantity,
            user=user,
            reference=reference
        )