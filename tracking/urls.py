from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("keg/", views.keg_dashboard_view, name="keg_dashboard"),
    path("keg/config/", views.keg_system_config_view, name="keg_config"),
    path("keg/policies/", views.business_keg_policy_view, name="business_keg_policy"),
    path("keg/fraud/", views.fraud_monitor_view, name="fraud_monitor"),
    path("keg/active-sessions/", views.active_keg_sessions_view, name="active_sessions"),
    path("keg/verifications/", views.keg_verifications_view, name="keg_verifications"),
    path("keg/test-flow/", views.test_keg_flow_view, name="test_keg"),
]