from django.urls import path
from . import views
from .views import business_profile
app_name = "business"

urlpatterns = [
    path("home/", views.business_home, name="home"),
    path("profile/", business_profile, name="profile"),
    path("counters/create/", views.counter_create, name="counter_create"),
    path("counters/<int:pk>/update/", views.counter_update, name="counter_update"),
    path("counters/<int:pk>/delete/", views.counter_delete, name="counter_delete"),
]