from django.db import models
from .enum import BookingStatus, PaymentStatus
from futsal.models import Futsal
from user.models import User
import uuid

class TimeSlot(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    futsal = models.ForeignKey(
        Futsal,
        on_delete=models.CASCADE,
        related_name="time_slots"
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["futsal", "start_time", "end_time"])
        ]

    def __str__(self):
        return f"{self.futsal.name} | {self.start_time} - {self.end_time}"

class Bookings(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    futsal = models.ForeignKey(
        Futsal,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    required_date = models.DateField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Snapshot price at booking time"
    )

    status = models.CharField(
        max_length=20,
        choices=[(tag.name, tag.value) for tag in BookingStatus],
        default=BookingStatus.PENDING.name
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[(tag.name, tag.value) for tag in PaymentStatus],
        default=PaymentStatus.PENDING.name
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["futsal", "required_date"]),
            models.Index(fields=["user", "status"])
        ]

    def __str__(self):
        return f"{self.futsal.name} | {self.user.username} | {self.required_date}"

def payment_proof_path(instance, filename):
    return f"payment_proofs/{instance.booking.user.uuid}/{filename}"

class PaymentProof(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.OneToOneField(
        Bookings,
        on_delete=models.CASCADE,
        related_name="payment_proof"
    )

    proof = models.ImageField(upload_to=payment_proof_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PaymentProof | {self.booking.uuid}"
    
class CancelFine(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.OneToOneField(
        Bookings,
        on_delete=models.CASCADE,
        related_name="cancel_fine"
    )

    fine = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final cancellation fine (snapshot)"
    )

    status = models.CharField(
        max_length=20,
        choices=[(tag.name, tag.value) for tag in PaymentStatus],
        default=PaymentStatus.PENDING.name
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CancelFine | {self.booking.uuid} | Rs {self.fine}"
    