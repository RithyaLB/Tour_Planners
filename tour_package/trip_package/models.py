from django.db import models

class Country(models.Model):
    country_id = models.AutoField(primary_key=True, db_column='country_id')
    country_name = models.CharField(max_length=100, db_column='country_name')

    def __str__(self):
        return self.country_name


class City(models.Model):
    city_id = models.AutoField(primary_key=True, db_column='city_id')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country')
    city_name = models.CharField(max_length=100, db_column='city_name')
    city_price = models.DecimalField(max_digits=25, decimal_places=2, db_column='city_price',blank=True, null=True)
    stay_duration = models.IntegerField(blank=True, null=True, db_column='stay_duration')

    def __str__(self):
        return self.city_name


class Spot(models.Model):
    spot_id = models.AutoField(primary_key=True, db_column='spot_id')
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city')
    spot_name = models.CharField(max_length=150, db_column='spot_name')
    description = models.TextField(blank=True, null=True, db_column='description')
    entry_fee = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True, db_column='entry_fee')
    timing = models.TimeField(blank=True, null=True, db_column='timing')
    duration = models.DecimalField(max_digits=25, decimal_places=4, blank=True, null=True, db_column='duration')
    day_no = models.IntegerField(blank=True, null=True, db_column='day_no')

    def __str__(self):
        return self.spot_name


class TourPackage(models.Model):
    package_id = models.AutoField(primary_key=True, db_column='package_id')
    package_name = models.CharField(max_length=150, unique=True, db_column='package_name')
    description = models.TextField(blank=True, null=True, db_column='description')
    duration_days = models.IntegerField(blank=True, null=True, db_column='duration_days')
    price = models.DecimalField(max_digits=25, decimal_places=2, db_column='price',blank=True, null=True)

    def __str__(self):
        return self.package_name


class PackageCity(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, db_column='package')
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city')
    sequence = models.IntegerField(blank=True, null=True, db_column='sequence')

    def __str__(self):
        return f"{self.package.package_name} - {self.city.city_name}"

class TripPackageUsers(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    first_name = models.CharField(max_length=100, db_column='first_name', blank=True, null=True)
    last_name = models.CharField(max_length=100, db_column='last_name', blank=True, null=True)
    email = models.CharField(max_length=150, unique=True, db_column='email', blank=True, null=True)
    phone_number = models.CharField(max_length=15, db_column='phone_number', blank=True, null=True)
    password_hash = models.CharField(max_length=255, db_column='password_hash', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', blank=True, null=True)

    def _str_(self):
        return f"{self.first_name} {self.last_name}"


class TripPackageBookings(models.Model):
    booking_id = models.AutoField(primary_key=True, db_column='booking_id')
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, db_column='package')
    user = models.ForeignKey(TripPackageUsers, on_delete=models.CASCADE, db_column='user_id')
    booking_date = models.DateTimeField(auto_now_add=True, db_column='booking_date', blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_amount', blank=True, null=True)
    status = models.CharField(max_length=10, db_column='status', blank=True, null=True)

    def _str_(self):
        return f"Booking {self.booking_id} - {self.user.first_name}"


class TripPackagePassengers(models.Model):
    passenger_id = models.AutoField(primary_key=True, db_column='passenger_id')
    booking = models.ForeignKey(TripPackageBookings, on_delete=models.CASCADE, db_column='booking_id')
    full_name = models.CharField(max_length=100, db_column='full_name', blank=True, null=True)
    age = models.IntegerField(blank=True, null=True, db_column='age')
    gender = models.CharField(max_length=10, db_column='gender', blank=True, null=True)
    passport_number = models.CharField(max_length=20, db_column='passport_number', blank=True, null=True)

    def _str_(self):
        return self.full_name


class BookingTickets(models.Model):
    ticket_id = models.AutoField(primary_key=True, db_column='ticket_id')
    booking = models.ForeignKey(TripPackageBookings, on_delete=models.CASCADE, db_column='booking')

    def _str_(self):
        return f"Ticket {self.ticket_id} for Booking {self.booking.booking_id}"