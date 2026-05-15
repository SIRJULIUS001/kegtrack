# core/urls.py
from django.urls import path
from . import views
app_name = "core"
urlpatterns = [
    path("", views.index, name="index"),
    path("superadmin/business/", views.business_list, name="business_list"),
    path("superadmin/business/create/", views.business_create, name="business_create"),
    path("superadmin/business/<int:pk>/edit/", views.business_edit, name="business_edit"),
    path("superadmin/business/<int:pk>/toggle/", views.business_toggle, name="business_toggle"),
    path("superadmin/business/<int:pk>/impersonate/", views.impersonate_business, name="business_impersonate"),
    path("superadmin/business/exit/", views.exit_impersonation, name="exit_impersonation"),
    path("settings/", views.system_settings_view, name="system_settings"),
    path("audit-logs/", views.audit_logs_view, name="audit_logs"),
]
