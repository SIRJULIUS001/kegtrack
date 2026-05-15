from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("superadmin/", views.superadmin_home, name="superadmin_home"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/assign/", views.assign_staff, name="assign_staff"),
    path("staff/<int:user_id>/toggle/", views.toggle_staff_status, name="toggle_staff"),
    path("unauthorized/", views.unauthorized_view, name="unauthorized"),
    path("staff/<int:user_id>/remove/", views.remove_staff, name="remove_staff"),
    path("staff/<int:user_id>/remove/confirm/", views.remove_staff_confirm, name="remove_staff_confirm"),
    #global roles urls
    path("roles/", views.role_list, name="role_list"),
    path("roles/create/", views.role_create, name="role_create"),
    path("roles/<int:role_id>/edit/", views.role_edit, name="role_edit"),
    path("roles/<int:role_id>/permissions/", views.update_role_permissions, name="update_role_permissions"),
    
]