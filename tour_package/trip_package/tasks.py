from django.utils.timezone import now
from .models import TripPackageBookings

def update_booking_status():
    current_time = now()
    bookings = TripPackageBookings.objects.all()
    for booking in bookings:
        if booking.status == "cancelled":
            continue
        if booking.booking_date and booking.end_date:
            if booking.end_date < current_time:
                booking.status = "completed"
            elif booking.booking_date > current_time:
                booking.status = "confirmed"
            else:
                booking.status = "inprogress"
        else:
            booking.status = "confirmed"  
        booking.save()
        print(booking.id, booking.status)

