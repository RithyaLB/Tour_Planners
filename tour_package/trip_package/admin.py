from django.contrib import admin
from .models import *

admin.site.register(Country)
admin.site.register(City)
admin.site.register(Spot)
admin.site.register(TourPackage)
admin.site.register(PackageCity)
admin.site.register(TripPackageUsers)
admin.site.register(TripPackageBookings)
admin.site.register(TripPackagePassengers)
admin.site.register(BookingTickets)

