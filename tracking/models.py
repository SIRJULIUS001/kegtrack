from django.db import models

# Create your models here.
class KegSystemConfig(models.Model):

    enable_keg_tracking = models.BooleanField(default=True)
    force_verification = models.BooleanField(default=True)

    require_photo_proof = models.BooleanField(default=True)
    require_weight_check = models.BooleanField(default=True)

    live_camera_only = models.BooleanField(default=True)

    variance_threshold_percent = models.FloatField(default=2.0)
    beer_density = models.FloatField(default=1.01)

    def save(self, *args, **kwargs):
        self.pk = 1  # force single row
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global Keg Configuration"
    
class BusinessKegPolicy(models.Model):

    business = models.OneToOneField("business.Business", on_delete=models.CASCADE)

    allow_keg_tracking = models.BooleanField(default=True)
    max_variance_percent = models.FloatField(default=3.0)

    strict_verification = models.BooleanField(default=True)
    auto_lock_on_fraud = models.BooleanField(default=False)

    def __str__(self):
        return f"Policy - {self.business.name}"
    
class KegFraudSignal(models.Model):

    business = models.OneToOneField("business.Business", on_delete=models.CASCADE)

    total_variance = models.FloatField(default=0)
    fraud_score = models.FloatField(default=0)

    flagged = models.BooleanField(default=False)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fraud Signal - {self.business.name}"
    
class KegType(models.Model):

    TYPE_CHOICES = [
        ("regular", "Regular Keg"),
        ("dark", "Dark keg"),
    ]

    name = models.CharField(max_length=100)  # Tusker, Guinness
    beer_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    capacity_litres = models.FloatField()
    empty_weight = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.capacity_litres}L - {self.beer_type})"
    
class Keg(models.Model):

    business = models.ForeignKey("business.Business", on_delete=models.CASCADE)

    serial_number = models.CharField(max_length=100, unique=True)

    keg_type = models.ForeignKey(KegType, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.serial_number
    
from django.db import models
from tracking.models import Keg


class KegSession(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    keg = models.ForeignKey(Keg, on_delete=models.CASCADE)

    opened_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True
    )

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="open"
    )

    # =========================
    # CORE TRACKING FIELDS
    # =========================
    consumed_volume = models.FloatField(default=0)

    expected_remaining_litres = models.FloatField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["opened_at"]),
            models.Index(fields=["keg"]),
        ]

    def __str__(self):
        return f"{self.keg.serial_number} ({self.status})"
    
class KegVerification(models.Model):

    TRIGGER_CHOICES = [
        ("shift_end", "Shift End"),
        ("keg_empty", "Keg Empty"),
    ]

    keg = models.ForeignKey(Keg, on_delete=models.CASCADE)

    session = models.ForeignKey(KegSession, on_delete=models.CASCADE)

    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)

    measured_weight = models.FloatField()

    calculated_litres = models.FloatField()

    variance = models.FloatField()

    photo = models.ImageField(upload_to="keg_verifications/")

    verified_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.keg.serial_number} - {self.trigger}"