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
