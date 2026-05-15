from django.db import models

class POSSession(models.Model):

    business = models.ForeignKey("business.Business", on_delete=models.CASCADE)
    opened_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)

    is_active = models.BooleanField(default=True)

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
class POSItem(models.Model):

    business = models.ForeignKey("business.Business", on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    price = models.FloatField()

    keg_type = models.ForeignKey("tracking.KegType", on_delete=models.SET_NULL, null=True)

    volume_per_unit = models.FloatField(default=0.5)  # e.g. 0.5L beer
    
class POSTransaction(models.Model):

    session = models.ForeignKey("POSSession", on_delete=models.CASCADE)
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE)

    product = models.ForeignKey("inventory.Product", on_delete=models.SET_NULL, null=True)
    
    quantity = models.IntegerField(default=1)

    unit_price = models.FloatField()
    total_price = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)