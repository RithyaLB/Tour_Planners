from django.contrib import admin
from .models import Country, City, Spot, TourPackage, PackageCity

admin.site.register(Country)
admin.site.register(City)
admin.site.register(Spot)
admin.site.register(TourPackage)
admin.site.register(PackageCity)
