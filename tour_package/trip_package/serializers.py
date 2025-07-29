from rest_framework import serializers
from .models import *

class Country_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class City_Serializer(serializers.ModelSerializer):
    country = Country_Serializer(read_only=True)
    class Meta:
        model = City
        fields = '__all__'

class Spot_Serializer(serializers.ModelSerializer):
    city = City_Serializer(read_only=True)
    class Meta:
        model = Spot
        fields = '__all__'

class TourPackage_Serializer(serializers.ModelSerializer):
    class Meta:
        model = TourPackage
        fields = '__all__'

class PackageCity_Serializer(serializers.ModelSerializer):
    city = City_Serializer(read_only=True)
    package = TourPackage_Serializer(read_only=True)

    class Meta:
        model = PackageCity
        fields = '__all__'
