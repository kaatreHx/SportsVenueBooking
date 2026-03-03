from datetime import datetime
from decimal import Decimal
from django.utils.timezone import now, make_aware


def calculate_cancellation_fine(booking):
    """
    Calculate cancellation fine for a booking
    Returns Decimal fine amount
    """

    # 1️⃣ Booking start datetime
    booking_start = make_aware(
        datetime.combine(
            booking.required_date,
            booking.time_slot.start_time
        )
    )

    current_time = now()

    # 2️⃣ If booking already started → full fine
    if current_time >= booking_start:
        return booking.total_price

    # 3️⃣ Hours left before start
    hours_left = (booking_start - current_time).total_seconds() / 3600

    # 4️⃣ Fine rules
    if hours_left <= 2:
        return booking.total_price * Decimal("0.30")

    if hours_left <= 4:
        return booking.total_price * Decimal("0.15")

    return Decimal("0.00")