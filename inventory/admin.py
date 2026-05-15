from django.contrib import admin
from .models import (
    ProductCategory,
    Product,
    ProductVariant,
    LocationPoint,
    StockAtLocation
)
# Register your models here.

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
    list_filter = ("category",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "volume")
    list_filter = ("volume",)


@admin.register(LocationPoint)
class LocationPointAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "business", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)


@admin.register(StockAtLocation)
class StockAtLocationAdmin(admin.ModelAdmin):
    list_display = ("location", "variant", "quantity", "reserved_quantity", "updated_at")
    list_filter = ("location",)
    search_fields = ("location__name", "variant__product__name")