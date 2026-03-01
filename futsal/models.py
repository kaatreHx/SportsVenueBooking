from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
import uuid
# from attachment.models import Attachment

class Futsal(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name = models.CharField(max_length=150)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS longitude"
    )
    # images = GenericRelation(Attachment)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100)
    contact_number_primary = models.CharField(max_length=15)
    contact_number_secondary = models.CharField(max_length=15, blank=True, null=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
