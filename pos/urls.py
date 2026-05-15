from django.urls import path                         
from .views import superadmin_pos_dashboard
app_name = "pos"
from . import views 
urlpatterns = [
    path("superadmin/", superadmin_pos_dashboard, name="superadmin_dashboard"),
    path("terminal/", views.pos_terminal, name="terminal"),
    #path("session/open/", session_views.open_pos_session_view, name="open_session"),
    #path("session/close/", session_views.close_pos_session_view, name="close_session"),

    # sales
    #path("sale/create/", sales_views.create_sale_view, name="create_sale"),

    # dashboards
    #path("dashboard/", dashboard_views.pos_dashboard_view, name="dashboard"),
    path("terminal/", views.pos_terminal, name="terminal"),

    path(
        "search-products/",
        views.search_products,
        name="search_products"
    ),

    path(
        "products/",
        views.product_list,
        name="product_list"
    ),

    path(
        "add-to-cart/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "cart/",
        views.cart_partial,
        name="cart_partial"
    ),

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "kegs/",
        views.keg_panel,
        name="keg_panel"
    ),

    path(
        "activity-feed/",
        views.activity_feed,
        name="activity_feed"
    ),
   
]