from django.db import models
from django.conf import settings
from business.models import Business

class AuditLog(models.Model):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)

    changes = models.JSONField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.model_name}"
    
    
class SystemSetting(models.Model):

    # =========================
    # KEG / INVENTORY DEFAULTS
    # =========================
    default_keg_weight = models.FloatField(default=50)
    beer_density = models.FloatField(default=1.0)

    UNIT_CHOICES = [
        ("L", "Litres"),
        ("ML", "Millilitres"),
    ]
    volume_unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default="L")

    # =========================
    # FEATURE TOGGLES
    # =========================
    enable_pos = models.BooleanField(default=False)
    enable_keg_tracking = models.BooleanField(default=False)
    enable_analytics = models.BooleanField(default=False)
    enable_whatsapp = models.BooleanField(default=False)

    # =========================
    # BUSINESS RULES
    # =========================
    allow_self_registration = models.BooleanField(default=False)
    max_staff_per_business = models.IntegerField(default=20)
    trial_days = models.IntegerField(default=14)
    auto_disable_inactive = models.BooleanField(default=True)

    # =========================
    # SECURITY
    # =========================
    force_password_change = models.BooleanField(default=True)
    session_timeout = models.IntegerField(default=30)  # minutes
    allow_multi_login = models.BooleanField(default=False)
    track_login_meta = models.BooleanField(default=True)

    # =========================
    # RBAC CONTROL
    # =========================
    lock_system_roles = models.BooleanField(default=False)
    force_role_sync = models.BooleanField(default=False)

    # =========================
    # NOTIFICATIONS
    # =========================
    enable_email_notifications = models.BooleanField(default=True)
    notify_low_stock = models.BooleanField(default=True)
    notify_keg_loss = models.BooleanField(default=True)
    notify_suspicious_activity = models.BooleanField(default=True)

    # =========================
    # AUDIT LOGS
    # =========================
    enable_audit_logs = models.BooleanField(default=True)

    LOG_LEVELS = [
        ("minimal", "Minimal"),
        ("detailed", "Detailed"),
    ]
    audit_log_level = models.CharField(max_length=10, choices=LOG_LEVELS, default="detailed")
    audit_retention_days = models.IntegerField(default=30)

    # =========================
    # BRANDING
    # =========================
    system_name = models.CharField(max_length=100, default="KEGTRACK")
    logo = models.ImageField(upload_to="branding/", null=True, blank=True)
    theme_color = models.CharField(max_length=20, default="#4F46E5")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"