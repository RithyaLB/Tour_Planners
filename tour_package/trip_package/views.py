from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from datetime import datetime,timedelta
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import make_password, check_password
import requests

def call_flight_service(content, api_url):
    response = requests.post(api_url, json=content)
    response.raise_for_status()  
    return list(response.json())

@api_view(['POST'])
def register_user(request):
    """API to register a new user."""
    data = request.data.copy()

    if not data.get('email') or not data.get('password'):
        return Response({"error": "Email and Password are required"}, status=status.HTTP_400_BAD_REQUEST)

    if TripPackageUsers.objects.filter(email=data['email']).exists():
        return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

    # Hash the password
    data['password_hash'] = make_password(data.pop('password'))

    serializer = TripPackageUsers_Serializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    """API to authenticate user login."""
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email and Password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(email=email)
    except TripPackageUsers.DoesNotExist:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

    if check_password(password, user.password_hash):
        serializer = TripPackageUsers_Serializer(user)
        return Response({
            "message": "Login successful",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_details(request):
    """API to get user details using user_id."""
    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = TripPackageUsers_Serializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_user_details(request):
    """API to update user details using user_id."""
    user_id = request.data.get('user_id')

    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # If email is being changed, validate uniqueness
    new_email = request.data.get('email')
    if new_email and new_email != user.email:
        if TripPackageUsers.objects.filter(email=new_email).exclude(user_id=user_id).exists():
            return Response({"error": "Email is already in use"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TripPackageUsers_Serializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User details updated successfully", "user": serializer.data}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def change_password(request):
    """API to change user password using user_id, old password, and new password."""
    user_id = request.data.get('user_id')
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not all([user_id, old_password, new_password]):
        return Response({"error": "user_id, old password, and new password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if not check_password(old_password, user.password_hash):
        return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    user.password_hash = make_password(new_password)
    user.save()

    return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

def external_start_flight(budget,start_date,starting_place,head_count):
        matching_package = []
        package_cities = PackageCity.objects.filter(package__price__lt = budget,sequence = 1).order_by('package__package_id')
        if package_cities:
            for pc in package_cities:
                if starting_place != pc.city.city_name:
                    start = {
                        "travel_datetime": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                        "source_city": starting_place,
                        "destination_city": pc.city.city_name,
                        "seats_required" : head_count,
                        "limit": 5
                    }
                    flight_options = call_flight_service(start,"http://192.168.220.24:8080/flights/search")
                    '''flight_options = [
                                {
                                    "total_duration_minutes": 340,
                                    "total_price": 6100.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL201",
                                        "airline_name": "SpiceJet",
                                        "flight_number": "SG301",
                                        "source_airport": "DEL",
                                        "destination_airport": "HYD",
                                        "departure_time": "2025-07-30  07:00:00",
                                        "arrival_time": "2025-07-30 08:45:00",
                                        "duration_minutes": 105,
                                        "base_price": 2300.00,
                                        "available_seats": 7
                                    },
                                    {
                                        "flight_id": "FL305",
                                        "airline_name": "Vistara",
                                        "flight_number": "UK410",
                                        "source_airport": "HYD",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 10:00:00",
                                        "arrival_time": "2025-07-30 11:55:00",
                                        "duration_minutes": 115,
                                        "base_price": 2800.00,
                                        "available_seats": 7
                                    }
                                    ]
                                },
                                {
                                    "total_duration_minutes": 375,
                                    "total_price": 5500.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL202",
                                        "airline_name": "IndiGo",
                                        "flight_number": "6E789",
                                        "source_airport": "DEL",
                                        "destination_airport": "MAA",
                                        "departure_time": "2025-07-30 06:30:00",
                                        "arrival_time": "2025-07-30 08:20:00",
                                        "duration_minutes": 110,
                                        "base_price": 2500.00,
                                        "available_seats": 8
                                    },
                                    {
                                        "flight_id": "FL312",
                                        "airline_name": "Air India",
                                        "flight_number": "AI222",
                                        "source_airport": "MAA",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 09:45:00",
                                        "arrival_time": "2025-07-30 11:20:00",
                                        "duration_minutes": 95,
                                        "base_price": 3000.00,
                                        "available_seats": 8
                                    }
                                    ]
                                }
                                ]'''
                    if not flight_options:
                        continue
                    cheapest_option = min(flight_options,key=lambda f: float(f.get("total_price", float("inf"))))
                    min_flight_price = float(cheapest_option.get("total_price", 0))
                    package_price = float(pc.package.price or 0)
                    total_cost = package_price + min_flight_price
                    if total_cost <= budget:
                        flights = cheapest_option.get("flights", [])
                        if flights:
                            last_flight = flights[-1]
                            arrival_time_str = last_flight.get("arrival_time")
                            arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%dT%H:%M:%S")
                            matching_package.append({
                                "package_id": pc.package.package_id,
                                "min_flight_price": total_cost,
                                "arrival_time": arrival_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(arrival_time, datetime) else arrival_time
                            })
        return matching_package

def internal_flight(matching_package,budget,head_count,start_date):
    final_packages = []
    for mp in matching_package:
        package_id = mp["package_id"]
        package_cities = list(PackageCity.objects.filter(package__package_id=package_id).order_by('sequence'))
        arrival_str = mp["arrival_time"]
        arrival_dt = datetime.strptime(arrival_str, "%Y-%m-%d %H:%M:%S")
        current_date = (arrival_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        valid = True
        min_flight_price = mp["min_flight_price"]
        added_price = min_flight_price
        for i in range(len(package_cities) - 1):  
            current_pc = package_cities[i]
            next_pc = package_cities[i + 1]
            city_start_date = current_date
            spots = Spot.objects.filter(city=current_pc.city).order_by('-day_no','timing')
            if not spots.exists():
                valid = False
                break  
            latest_spot = spots.first()
            day_no = latest_spot.day_no or 0
            day_no = day_no - 1
            timing = latest_spot.timing 
            duration_hours = float(latest_spot.duration or 0)
            target_date = city_start_date + timedelta(days=day_no)
            city_end_datetime = datetime.combine(target_date, timing) + timedelta(hours=duration_hours)
            city_dict = {
                "travel_datetime": city_end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "source_city": current_pc.city.city_name,
                "destination_city": next_pc.city.city_name,
                "seats_required": head_count,
                "limit": 1,
            }
            flights = call_flight_service(city_dict,"http://192.168.220.24:8080/flights/internal-search")
            '''flights = [
                    {
                        "flight_id": "FL123",
                        "airline_name": "IndiGo",
                        "flight_number": "6E456",
                        "source_airport": "DEL",
                        "source_city": "New Delhi",
                        "destination_airport": "BOM",
                        "destination_city": "Mumbai",
                        "departure_time": "2025-07-30 08:30:00",
                        "arrival_time": "2025-07-30 10:45:00",
                        "duration_minutes": 135,
                        "base_price": 3200.00,
                        "available_seats": 12
                    }
                    ]'''
            if not flights:
                valid = False
                break
            arrival_time_str = flights[0].get("arrival_time")
            last_arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M:%S")
            current_date = (last_arrival_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            base_price = float(flights[0].get("base_price", 0))
            added_price += base_price
        if valid and added_price < budget:
            last_city = package_cities[-1].city
            last_spots = Spot.objects.filter(city=last_city).order_by('-day_no','timing')
            if last_spots.exists():
                last_spot = last_spots.first()
                last_day_no = last_spot.day_no or 0
                timing = last_spot.timing
                duration_hours = float(last_spot.duration or 0)
                finish_date = current_date + timedelta(days=(last_day_no - 1))
                finish_time_dt = datetime.combine(finish_date, timing) + timedelta(hours=duration_hours)
                final_packages.append({
                    "package_id": package_id,
                    "total_price": added_price,
                    "finish_time": finish_time_dt.strftime("%Y-%m-%dT%H:%M:%S")
                })
    return final_packages

def external_end_flight(matching_package,budget,starting_place,head_count):
    package = []
    for mc in matching_package:
        package_cities = PackageCity.objects.filter(package__package_id=mc['package_id']).order_by('-sequence').first()
        send = {
            "travel_datetime": mc["finish_time"],
            "source_city": package_cities.city.city_name,
            "destination_city": starting_place,
            "seats_required" : head_count,
            "limit": 5,
        }
        flight_options = call_flight_service(send,"http://192.168.220.24:8080/flights/search")
        '''flight_options = [
                                {
                                    "total_duration_minutes": 340,
                                    "total_price": 6100.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL201",
                                        "airline_name": "SpiceJet",
                                        "flight_number": "SG301",
                                        "source_airport": "DEL",
                                        "destination_airport": "HYD",
                                        "departure_time": "2025-07-30  07:00:00",
                                        "arrival_time": "2025-07-30 08:45:00",
                                        "duration_minutes": 105,
                                        "base_price": 2300.00,
                                        "available_seats": 7
                                    },
                                    {
                                        "flight_id": "FL305",
                                        "airline_name": "Vistara",
                                        "flight_number": "UK410",
                                        "source_airport": "HYD",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 10:00:00",
                                        "arrival_time": "2025-07-30 11:55:00",
                                        "duration_minutes": 115,
                                        "base_price": 2800.00,
                                        "available_seats": 7
                                    }
                                    ]
                                },
                                {
                                    "total_duration_minutes": 375,
                                    "total_price": 5500.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL202",
                                        "airline_name": "IndiGo",
                                        "flight_number": "6E789",
                                        "source_airport": "DEL",
                                        "destination_airport": "MAA",
                                        "departure_time": "2025-07-30 06:30:00",
                                        "arrival_time": "2025-07-30 08:20:00",
                                        "duration_minutes": 110,
                                        "base_price": 2500.00,
                                        "available_seats": 8
                                    },
                                    {
                                        "flight_id": "FL312",
                                        "airline_name": "Air India",
                                        "flight_number": "AI222",
                                        "source_airport": "MAA",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 09:45:00",
                                        "arrival_time": "2025-07-30 11:20:00",
                                        "duration_minutes": 95,
                                        "base_price": 3000.00,
                                        "available_seats": 8
                                    }
                                    ]
                                }
                                ]'''
        if not flight_options:
            continue
        cheapest_option = min(flight_options,key=lambda f: float(f.get("total_price", float("inf"))))
        min_flight_price = float(cheapest_option.get("total_price", 0))
        total_cost = mc["total_price"] + min_flight_price
        if total_cost <= budget:
            temp = {
                "package_id" : mc["package_id"],
                "total_price" : total_cost
            }
            package.append(temp)
    return package

def get_formatted_package(matching_package):
    package_ids = [pkg['package_id'] for pkg in matching_package]
    package_cities = PackageCity.objects.select_related('package', 'city__country') \
        .prefetch_related('city__spot_set') \
        .filter(package__package_id__in=package_ids) \
        .order_by('package__package_id', 'sequence')
    package_group = {}
    for pc in package_cities:
        package = pc.package
        city = pc.city
        spots = Spot.objects.filter(city=city)
        if not spots.exists():
            continue
        if package.package_id not in package_group:
            package_data = model_to_dict(package)
            package_data['total_price'] = next(
                (p['total_price'] for p in matching_package if p['package_id'] == package.package_id), None
            )
            package_data['cities'] = []
            package_group[package.package_id] = package_data
        city_data = model_to_dict(city)
        city_data['country_name'] = city.country.country_name
        city_data['spots'] = [model_to_dict(spot) for spot in spots]
        package_group[package.package_id]['cities'].append(city_data)
    package_list = list(package_group.values())
    return package_list

@api_view(['POST'])
def filter_package(request):
    budget = request.data.get('budget')
    start_date = request.data.get('start_date')
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    starting_place = request.data.get('starting_place')
    head_count = request.data.get('head_count')
    if budget and start_date and starting_place and head_count:
        #Call external start_flight
        matching_package = external_start_flight(budget,start_date,starting_place,head_count)
        #Call internal flight
        matching_package = internal_flight(matching_package,budget,head_count, start_date)
        #Call external end_flight
        matching_package = external_end_flight(matching_package,budget,starting_place,head_count)
        #Call get_formatted_package
        formatted_package = get_formatted_package(matching_package)
        return Response(formatted_package, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Budget is required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def start_flight_options(request):
    try:
        package_id = request.data.get('package_id')
        start_date_str = request.data.get('package_date')
        starting_place = request.data.get('customer_source')
        head_count = int(request.data.get('head_count'))
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        package_cities = PackageCity.objects.filter(package__package_id=package_id,sequence=1)
        matching_package = []
        for pc in package_cities:
            if starting_place != pc.city.city_name:
                start = {
                    "travel_datetime": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "source_city": starting_place,
                    "destination_city": pc.city.city_name,
                    "seats_required": head_count,
                    "limit": 5
                }
                flight_options = call_flight_service(start,"http://192.168.220.24:8080/flights/search")
                '''flight_options = [
                                {
                                    "total_duration_minutes": 340,
                                    "total_price": 6100.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL201",
                                        "airline_name": "SpiceJet",
                                        "flight_number": "SG301",
                                        "source_airport": "DEL",
                                        "destination_airport": "HYD",
                                        "departure_time": "2025-07-30  07:00:00",
                                        "arrival_time": "2025-07-30 08:45:00",
                                        "duration_minutes": 105,
                                        "base_price": 2300.00,
                                        "available_seats": 7
                                    },
                                    {
                                        "flight_id": "FL305",
                                        "airline_name": "Vistara",
                                        "flight_number": "UK410",
                                        "source_airport": "HYD",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 10:00:00",
                                        "arrival_time": "2025-07-30 11:55:00",
                                        "duration_minutes": 115,
                                        "base_price": 2800.00,
                                        "available_seats": 7
                                    }
                                    ]
                                },
                                {
                                    "total_duration_minutes": 375,
                                    "total_price": 5500.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL202",
                                        "airline_name": "IndiGo",
                                        "flight_number": "6E789",
                                        "source_airport": "DEL",
                                        "destination_airport": "MAA",
                                        "departure_time": "2025-07-30 06:30:00",
                                        "arrival_time": "2025-07-30 08:20:00",
                                        "duration_minutes": 110,
                                        "base_price": 2500.00,
                                        "available_seats": 8
                                    },
                                    {
                                        "flight_id": "FL312",
                                        "airline_name": "Air India",
                                        "flight_number": "AI222",
                                        "source_airport": "MAA",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 09:45:00",
                                        "arrival_time": "2025-07-30 11:20:00",
                                        "duration_minutes": 95,
                                        "base_price": 3000.00,
                                        "available_seats": 8
                                    }
                                    ]
                                }
                                ]'''
        return Response(flight_options, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def generate_flight_plan(request):
    try:
        head_count = int(request.data.get("head_count"))
        package_id = int(request.data.get("package_id"))
        arrival_str = request.data.get("src_to_first_arrival_time")
        source = request.data.get("source")

        if not all([head_count, package_id, arrival_str, source]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        arrival_dt = datetime.strptime(arrival_str, "%Y-%m-%dT%H:%M")
        current_date = (arrival_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        package_cities = list(PackageCity.objects.filter(package__package_id=package_id).order_by('sequence'))
        if not package_cities or len(package_cities) < 1:
            return Response({"error": "No cities in the package"}, status=status.HTTP_400_BAD_REQUEST)

        result = []          
        spot_itinerary = []  
        for i in range(len(package_cities) - 1):
            current_pc = package_cities[i]
            next_pc = package_cities[i + 1]
            spots = Spot.objects.filter(city=current_pc.city).order_by('-day_no','-timing')
            if not spots.exists():
                return Response({"error": f"No spots found in {current_pc.city.city_name}"}, status=status.HTTP_400_BAD_REQUEST)

            latest_spot = spots.first()
            day_no = (latest_spot.day_no or 1) - 1
            timing = latest_spot.timing
            duration_hours = float(latest_spot.duration or 0)
            target_date = current_date + timedelta(days=day_no)
            last_spot_end_time = datetime.combine(target_date, timing) + timedelta(hours=duration_hours)
            city_dict = {
                "travel_datetime": last_spot_end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "source_city": current_pc.city.city_name,
                "destination_city": next_pc.city.city_name,
                "seats_required": head_count,
                "limit": 1
            }
            flights = call_flight_service(city_dict,"http://192.168.220.24:8080/flights/internal-search")
            '''flights = [
                {
                    "flight_id": "FL123",
                    "airline_name": "IndiGo",
                    "flight_number": "6E456",
                    "source_airport": "DEL",
                    "source_city": "New Delhi",
                    "destination_airport": "BOM",
                    "destination_city": "Mumbai",
                    "departure_time": "2025-07-30 08:30:00",
                    "arrival_time": "2025-07-30 10:45:00",
                    "duration_minutes": 135,
                    "base_price": 3200.00,
                    "available_seats": 12
                }
            ]'''

            if not flights:
                return Response({"error": f"No flights from {current_pc.city.city_name} to {next_pc.city.city_name}"}, status=status.HTTP_400_BAD_REQUEST)
            arrival_time_str = flights[0].get("arrival_time")
            last_arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%dT%H:%M:%S")
            current_date = last_arrival_time  
            city_dict["flight"] = flights[0]
            result.append(city_dict)
        current_date = (arrival_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(len(package_cities)):
            current_pc = package_cities[i]

            city_spots = Spot.objects.filter(city=current_pc.city).order_by('day_no', 'timing')
            if not city_spots.exists():
                continue

            city_spot_schedule = []
            day_start = current_date
            current_time = datetime.combine(day_start, datetime.min.time())

            for spot in city_spots:
                spot_day_no = spot.day_no or 1 
                visit_date = current_date + timedelta(days=spot_day_no - 1)

                start_time = datetime.combine(visit_date, spot.timing or datetime.min.time())
                end_time = start_time + timedelta(hours=float(spot.duration or 0))

                city_spot_schedule.append({
                    "spot_id": spot.spot_id,
                    "spot_name": spot.spot_name,
                    "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M")
                })

                current_time = end_time

            spot_itinerary.append({
                "city_id": current_pc.city.city_id,
                "city_name": current_pc.city.city_name,
                "spots": city_spot_schedule
            })
            if i < len(result):
                arrival_time_str = result[i]['flight']['arrival_time']
                last_arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%dT%H:%M:%S")
                current_date = (last_arrival_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        return Response({
            "flight_plan": result,
            "spot_schedule": spot_itinerary
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def end_flight_options(request):
    try:
        spot_id = request.data.get("spot_id")
        package_id = request.data.get("package_id")
        head_count = int(request.data.get("head_count"))
        end_datetime_str = request.data.get("package_date_end_date_time")
        destination = request.data.get("customer_destination")
        if not all([spot_id, package_id, head_count, end_datetime_str, destination]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return Response({"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            spot = Spot.objects.select_related('city').get(spot_id=spot_id)
            source_city_name = spot.city.city_name
        except Spot.DoesNotExist:
            return Response({"error": "Spot not found"}, status=status.HTTP_404_NOT_FOUND)
        city_dict = {
            "travel_datetime": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_city": source_city_name,
            "destination_city": destination,
            "seats_required": head_count,
            "limit": 5
        }
        flight_options = call_flight_service(city_dict,"http://192.168.220.24:8080/flights/search")
        '''flight_options = [
                                {
                                    "total_duration_minutes": 340,
                                    "total_price": 6100.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL201",
                                        "airline_name": "SpiceJet",
                                        "flight_number": "SG301",
                                        "source_airport": "DEL",
                                        "destination_airport": "HYD",
                                        "departure_time": "2025-07-30  07:00:00",
                                        "arrival_time": "2025-07-30 08:45:00",
                                        "duration_minutes": 105,
                                        "base_price": 2300.00,
                                        "available_seats": 7
                                    },
                                    {
                                        "flight_id": "FL305",
                                        "airline_name": "Vistara",
                                        "flight_number": "UK410",
                                        "source_airport": "HYD",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 10:00:00",
                                        "arrival_time": "2025-07-30 11:55:00",
                                        "duration_minutes": 115,
                                        "base_price": 2800.00,
                                        "available_seats": 7
                                    }
                                    ]
                                },
                                {
                                    "total_duration_minutes": 375,
                                    "total_price": 5500.00,
                                    "flights": [
                                    {
                                        "flight_id": "FL202",
                                        "airline_name": "IndiGo",
                                        "flight_number": "6E789",
                                        "source_airport": "DEL",
                                        "destination_airport": "MAA",
                                        "departure_time": "2025-07-30 06:30:00",
                                        "arrival_time": "2025-07-30 08:20:00",
                                        "duration_minutes": 110,
                                        "base_price": 2500.00,
                                        "available_seats": 8
                                    },
                                    {
                                        "flight_id": "FL312",
                                        "airline_name": "Air India",
                                        "flight_number": "AI222",
                                        "source_airport": "MAA",
                                        "destination_airport": "BLR",
                                        "departure_time": "2025-07-30 09:45:00",
                                        "arrival_time": "2025-07-30 11:20:00",
                                        "duration_minutes": 95,
                                        "base_price": 3000.00,
                                        "available_seats": 8
                                    }
                                    ]
                                }
                                ]'''
        return Response(flight_options, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_booking(request):
    try:
        data = request.data
        package_id = data["package_id"]
        user_id = data["user_id"]
        head_count = data["head_count"]
        total_amount = data["flight_total"]
        passengers = data["passengers"]
        flights = data["flights"]
        booking_date_str = data["booking_date"]
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d")

        package = TourPackage.objects.get(package_id=package_id)
        user = TripPackageUsers.objects.get(user_id=user_id)
        booking = TripPackageBookings.objects.create(
            package=package,
            user=user,
            total_amount=(total_amount+package.price)*head_count,
            status="confirmed",
            booking_date=booking_date
        )
        for p in passengers:
            TripPackagePassengers.objects.create(
                booking=booking,
                full_name=p["name"],
                age=p["age"],
                gender=p["gender"],
                passport_number=p["passport_no"]
            )
        for flight in flights:
            flight_request = {
                "flight_id": flight["flight_id"],
                "travel_date": flight["departure_time"].split(" ")[0],  
                "seats_required": head_count,
                "passenger_details": passengers
            }
            flight_response = call_flight_service(flight_request,"http://192.168.220.24:8080/flights/book")
            '''flight_response = {
                "booking_id": 2,
                "status": "confirmed",
                "total_price": 9000.0,
                "message": "Successfully booked 2 seats"
                }'''
            BookingTickets.objects.create(
                    booking=booking,
                    flight_booking_id=flight_response.get("booking_id")
                )
        return Response({
            "message": "Booking and flight tickets successfully stored.",
            "booking_id": booking.booking_id
        }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
