from rest_framework import serializers
from .models import TimeSlot, Bookings, PaymentProof
from .enum import BookingStatus, PaymentStatus
from datetime import timedelta

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = "__all__"
        read_only_fields = ("uuid", "created_at")

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        futsal = attrs.get("futsal")

        # Handle update case
        if self.instance:
            start_time = start_time or self.instance.start_time
            end_time = end_time or self.instance.end_time
            futsal = futsal or self.instance.futsal

        # 1️⃣ Start must be before end
        if start_time >= end_time:
            raise serializers.ValidationError(
                "Start time must be before end time."
            )

        # 2️⃣ Minimum duration = 1 hour
        if end_time - start_time < timedelta(hours=1):
            raise serializers.ValidationError(
                "Time slot must be at least 1 hour long."
            )

        # 3️⃣ Overlapping check
        overlapping_slots = TimeSlot.objects.filter(
            futsal=futsal,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        # Exclude self during update
        if self.instance:
            overlapping_slots = overlapping_slots.exclude(
                pk=self.instance.pk
            )

        if overlapping_slots.exists():
            raise serializers.ValidationError(
                "This time slot overlaps with an existing time slot."
            )

        return attrs

    def create(self, validated_data):
        return TimeSlot.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class BookingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookings
        fields = '__all__'
        read_only_fields = ('uuid', 'status', 'payment_status', 'created_at')

    def create(self, validated_data):
        time_slot = validated_data.get('time_slot')
        timeSlotData = TimeSlot.objects.get(uuid=time_slot)
        timeSlotData.is_active = False
        timeSlotData.save()
        booking = Bookings.objects.create(**validated_data, total_price=timeSlotData.price)
        booking.status = BookingStatus.PENDING
        booking.payment_status = PaymentStatus.PENDING
        is_full_day = validated_data.get('is_full_day')
        if is_full_day:
            book_slot = TimeSlot.objects.filter(futsal=booking.futsal)
            for slot in book_slot:
                slot.is_active = False
                slot.save() 
            
        booking.save()
        return booking

    def update(self, instance, validated_data):
        time_slot = validated_data.get('time_slot')
        if time_slot:
            timeSlotData = TimeSlot.objects.get(uuid=time_slot)
            timeSlotData.is_active = False
            timeSlotData.save()
            instance.total_price = timeSlotData.price
            prev_time_slot = instance.time_slot
            prev_time_slot.is_active = True
            prev_time_slot.save()
            instance.time_slot = timeSlotData

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

class PaymentProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProof
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at')

    def create(self, validated_data):
        payment_proof = PaymentProof.objects.create(**validated_data)
        return payment_proof

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance