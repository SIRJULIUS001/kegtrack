from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("catalog/", views.catalog_dashboard, name="dashboard"),
    path("catalog/products/", views.product_list, name="product_list"),
    path("catalog/products/add/", views.product_create, name="product_create"),
    path("catalog/products/<int:pk>/edit/", views.product_update, name="product_update"),
    path("catalog/products/<int:pk>/delete/", views.product_delete, name="product_delete"),

    # VARIANTS
    path("catalog/variants/", views.variant_list, name="variant_list"),
    path("catalog/variants/add/", views.variant_create, name="variant_create"),
    
    path("dashboard/", views.business_inventory_dashboard, name="business_inventory_dashboard"),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/commit/", views.stock_commit, name="stock_commit"),
    path("stock-panel/", views.stock_panel, name="stock_panel"),
    path("cart/partial/", views.cart_partial, name="cart_partial"),
    path("products/search/", views.product_search, name="product_search"),
    path("stock/update/<int:stock_id>/", views.update_stock, name="update_stock"),
    path("stock/delete/<int:stock_id>/", views.delete_stock, name="delete_stock"),
]