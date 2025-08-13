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

class TripPackageUsers_Serializer(serializers.ModelSerializer):
    class Meta:
        model = TripPackageUsers
        exclude = ['password_hash']

class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPackagePassengers
        fields = ['passenger_id', 'full_name', 'age', 'gender', 'passport_number']

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTickets
        fields = ['ticket_id', 'flight_booking_id']

class BookingSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True, source='trippackagepassengers_set')
    tickets = TicketSerializer(many=True, source='bookingtickets_set')
    package = TourPackage_Serializer(read_only=True) 
    
    class Meta:
        model = TripPackageBookings
        fields = '__all__'