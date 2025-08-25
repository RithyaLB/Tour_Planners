import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from datetime import datetime, timedelta
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import make_password, check_password
import requests
import ssl
import hashlib
from django.utils import timezone

logger = logging.getLogger('flight_cancellation')

url = "https://192.168.161.64:443"
#url = "http://localhost:8080"

email_service_url = 'http://192.168.163.197:5000'
email_api_key = '0898c79d9edee1eaf79e1f97718ea84da47472f70884944ba1641b58ed24796c'

phone_api_key = '9D941AF69FAA5E041172D29A8B459BB4'
phone_service_url = 'http://192.168.160.245:3002'

def get_cert_fingerprint(cert_path: str) -> str:
    with open(cert_path, "rb") as f:
        cert_pem = f.read()
    cert_der = ssl.PEM_cert_to_DER_cert(cert_pem.decode())
    fingerprint = hashlib.sha1(cert_der).hexdigest().lower()
    logger.info(f"Generated certificate fingerprint from {cert_path}")
    return fingerprint


def call_flight_service(content, api_url):
    cert_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/django.crt"
    key_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/django.key"
    ca_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/ca.crt"

    fingerprint = get_cert_fingerprint(cert_path)
    headers = {
        "x-client-cert-fingerprint": fingerprint
    }

    logger.info(f"Calling flight service: {api_url} with payload: {content}")
    response = requests.post(
        api_url,
        json=content,
        cert=(cert_path, key_path),
        headers=headers,
        verify= False  # Use your CA file in production
    )

    logger.info(f"Flight service response status: {response.status_code}")
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        logger.warning(f"Flight service returned non-JSON response: {response.text}")
        return {"status": response.status_code, "message": response.text or "No content"}


@api_view(['POST'])
def register_user(request):
    """API to register a new user."""
    data = request.data.copy()
    logger.info(f"Register user request received: {data.get('email')}")
    logger.info(f"Data Recieved: {data}")

    if not data.get('email') or not data.get('password'):
        return Response({"error": "Email and Password are required"}, status=status.HTTP_400_BAD_REQUEST)

    if TripPackageUsers.objects.filter(email=data['email']).exists():
        logger.info(f"Registration failed: User with email {data['email']} already exists")
        return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

    data['password_hash'] = make_password(data.pop('password'))
    serializer = TripPackageUsers_Serializer(data=data)

    if serializer.is_valid():
        user = serializer.save()
        logger.info(f"User registered successfully: {user.user_id}")
        return Response({
            "message": "User registered successfully",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)

    logger.info(f"Registration failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    """API to authenticate user login."""
    email = request.data.get('email')
    password = request.data.get('password')
    logger.info(f"Login attempt for email: {email}")

    if not email or not password:
        return Response({"error": "Email and Password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(email=email)
    except TripPackageUsers.DoesNotExist:
        logger.info(f"Login failed: Invalid email {email}")
        return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

    if check_password(password, user.password_hash):
        serializer = TripPackageUsers_Serializer(user)
        logger.info(f"Login successful for user_id: {user.user_id}")
        return Response({
            "message": "Login successful",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    logger.info(f"Login failed: Incorrect password for email {email}")
    return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user_details(request):
    """API to get user details using user_id."""
    user_id = request.query_params.get('user_id')
    logger.info(f"Fetching user details for user_id: {user_id}")

    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        logger.info(f"User not found: user_id {user_id}")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = TripPackageUsers_Serializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_user_details(request):
    """API to update user details using user_id."""
    user_id = request.data.get('user_id')
    logger.info(f"Update request for user_id: {user_id}")

    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        logger.info(f"User not found: user_id {user_id}")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    new_email = request.data.get('email')
    if new_email and new_email != user.email:
        if TripPackageUsers.objects.filter(email=new_email).exclude(user_id=user_id).exists():
            logger.info(f"Email update failed: {new_email} already in use")
            return Response({"error": "Email is already in use"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TripPackageUsers_Serializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"User details updated successfully for user_id: {user_id}")
        return Response({"message": "User details updated successfully", "user": serializer.data}, status=status.HTTP_200_OK)

    logger.info(f"User update failed for user_id {user_id}: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def change_password(request):
    """API to change user password using user_id, old password, and new password."""
    user_id = request.data.get('user_id')
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    logger.info(f"Password change request for user_id: {user_id}")

    if not all([user_id, old_password, new_password]):
        return Response({"error": "user_id, old password, and new password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TripPackageUsers.objects.get(user_id=user_id)
    except TripPackageUsers.DoesNotExist:
        logger.info(f"Password change failed: User not found for user_id {user_id}")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if not check_password(old_password, user.password_hash):
        logger.info(f"Password change failed: Incorrect old password for user_id {user_id}")
        return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    user.password_hash = make_password(new_password)
    user.save()
    logger.info(f"Password changed successfully for user_id: {user_id}")
    return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

def external_start_flight(budget, start_date, starting_place, head_count):
    logger.info(f"[external_start_flight] budget={budget}, start_date={start_date}, starting_place={starting_place}, head_count={head_count}")
    matching_package = []
    package_cities = PackageCity.objects.filter(package__price__lt=budget, sequence=1).order_by('package__package_id')
    if package_cities:
        for pc in package_cities:
            if starting_place != pc.city.city_name:
                start = {
                    "travel_datetime": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "source_city": starting_place,
                    "destination_city": pc.city.city_name,
                    "seats_required": head_count,
                    "limit": 5
                }
                logger.info(f"[external_start_flight] Searching flights: {start}")
                flight_options = call_flight_service(start, f"{url}/flights/search")
                logger.info(f"[external_start_flight] Response from flight service: {flight_options}")

                if not flight_options:
                    continue
                cheapest_option = min(flight_options, key=lambda f: float(f.get("total_price", float("inf"))))
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
    logger.info(f"[external_start_flight] Matching packages: {matching_package}")
    return matching_package


def internal_flight(matching_package, budget, head_count, start_date):
    logger.info(f"[internal_flight] Input: {matching_package}, budget={budget}, head_count={head_count}, start_date={start_date}")
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
            spots = Spot.objects.filter(city=current_pc.city).order_by('-day_no', '-timing')
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
            logger.info(f"[internal_flight] Internal flight search payload: {city_dict}")
            flights = call_flight_service(city_dict, f"{url}/flights/internal-search")
            logger.info(f"[internal_flight] Internal flight search response: {flights}")

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
            last_spots = Spot.objects.filter(city=last_city).order_by('-day_no', '-timing')
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
    logger.info(f"[internal_flight] Final packages: {final_packages}")
    return final_packages


def external_end_flight(matching_package, budget, starting_place, head_count):
    logger.info(f"[external_end_flight] Input: {matching_package}, budget={budget}, starting_place={starting_place}, head_count={head_count}")
    package = []
    for mc in matching_package:
        package_cities = PackageCity.objects.filter(package__package_id=mc['package_id']).order_by('-sequence').first()
        send = {
            "travel_datetime": mc["finish_time"],
            "source_city": package_cities.city.city_name,
            "destination_city": starting_place,
            "seats_required": head_count,
            "limit": 5,
        }
        logger.info(f"[external_end_flight] Searching end flights: {send}")
        flight_options = call_flight_service(send, f"{url}/flights/search")
        logger.info(f"[external_end_flight] End flight search response: {flight_options}")
        
        if not flight_options:
            continue
        cheapest_option = min(flight_options, key=lambda f: float(f.get("total_price", float("inf"))))
        min_flight_price = float(cheapest_option.get("total_price", 0))
        total_cost = mc["total_price"] + min_flight_price
        if total_cost <= budget:
            temp = {
                "package_id": mc["package_id"],
                "total_price": total_cost
            }
            package.append(temp)
    logger.info(f"[external_end_flight] Final end-flight packages: {package}")
    return package


def get_formatted_package(matching_package):
    logger.info(f"[get_formatted_package] Input: {matching_package}")
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
    logger.info(f"[get_formatted_package] Output: {package_list}")
    return package_list


@api_view(['POST'])
def filter_package(request):
    logger.info(f"[filter_package] Request payload: {request.data}")
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
        logger.info(f"[filter_package] Final response: {formatted_package}")
        return Response(formatted_package, status=status.HTTP_200_OK)
    else:
        logger.info("[filter_package] Missing required parameters")
        return Response({'error': 'Budget is required'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def start_flight_options(request):
    logger.info(f"start_flight_options request payload: {request.data}")
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
                logger.info(f"Calling flight service with payload: {start}")
                flight_options = call_flight_service(start, f"{url}/flights/search")
                logger.info(f"Flight service response: {flight_options}")
        return Response(flight_options, status=status.HTTP_200_OK)
    except Exception as e:
        logger.info(f"Error in start_flight_options: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def generate_flight_plan(request):
    logger.info(f"generate_flight_plan request payload: {request.data}")
    try:
        head_count = int(request.data.get("head_count"))
        package_id = int(request.data.get("package_id"))
        arrival_str = request.data.get("src_to_first_arrival_time")
        source = request.data.get("source")

        if not all([head_count, package_id, arrival_str, source]):
            logger.info("Missing required fields in generate_flight_plan request")
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        arrival_dt = datetime.strptime(arrival_str, "%Y-%m-%dT%H:%M")
        current_date = (arrival_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        package_cities = list(PackageCity.objects.filter(package__package_id=package_id).order_by('sequence'))
        logger.info(f"Fetched package cities: {package_cities}")

        if not package_cities or len(package_cities) < 1:
            logger.info("No cities found in package")
            return Response({"error": "No cities in the package"}, status=status.HTTP_400_BAD_REQUEST)

        result = []          
        spot_itinerary = []  
        for i in range(len(package_cities) - 1):
            current_pc = package_cities[i]
            next_pc = package_cities[i + 1]
            spots = Spot.objects.filter(city=current_pc.city).order_by('-day_no', '-timing')
            logger.info(f"Spots for city {current_pc.city.city_name}: {list(spots)}")

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
            logger.info(f"Calling flight service with payload: {city_dict}")
            flights = call_flight_service(city_dict, f"{url}/flights/internal-search")
            logger.info(f"Flight service response: {flights}")

            if not flights:
                return Response({"error": f"No flights from {current_pc.city.city_name} to {next_pc.city.city_name}"}, status=status.HTTP_400_BAD_REQUEST)
            arrival_time_str = flights[0].get("arrival_time")
            last_arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M:%S")
            current_date = last_arrival_time  
            city_dict["flight"] = flights[0]
            result.append(city_dict)
        current_date = (arrival_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(len(package_cities)):
            current_pc = package_cities[i]

            city_spots = Spot.objects.filter(city=current_pc.city).order_by('day_no', 'timing')
            logger.info(f"Spot schedule for city {current_pc.city.city_name}: {list(city_spots)}")

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
                last_arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M:%S")
                current_date = (last_arrival_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        logger.info(f"Final generated flight plan: {result}")
        logger.info(f"Final generated spot itinerary: {spot_itinerary}")

        return Response({
            "flight_plan": result,
            "spot_schedule": spot_itinerary
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.info(f"Error in generate_flight_plan: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def end_flight_options(request):
    logger.info(f"end_flight_options request payload: {request.data}")
    try:
        spot_id = request.data.get("spot_id")
        package_id = request.data.get("package_id")
        head_count = int(request.data.get("head_count"))
        end_datetime_str = request.data.get("package_date_end_date_time")
        destination = request.data.get("customer_destination")
        if not all([spot_id, package_id, head_count, end_datetime_str, destination]):
            logger.info("Missing required fields in end_flight_options request")
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.info("Invalid datetime format in end_flight_options request")
            return Response({"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            spot = Spot.objects.select_related('city').get(spot_id=spot_id)
            source_city_name = spot.city.city_name
            logger.info(f"Fetched spot: {spot}, source city: {source_city_name}")
        except Spot.DoesNotExist:
            logger.info(f"Spot with ID {spot_id} not found")
            return Response({"error": "Spot not found"}, status=status.HTTP_404_NOT_FOUND)
        city_dict = {
            "travel_datetime": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_city": source_city_name,
            "destination_city": destination,
            "seats_required": head_count,
            "limit": 5
        }
        logger.info(f"Calling flight service with payload: {city_dict}")
        flight_options = call_flight_service(city_dict, f"{url}/flights/search")
        logger.info(f"Flight service response: {flight_options}")

        return Response(flight_options, status=status.HTTP_200_OK)

    except Exception as e:
        logger.info(f"Error in end_flight_options: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_booking(request):
    logger.info(f"Received create_booking request payload: {request.data}")
    try:
        data = request.data
        package_id = data["package_id"]
        user_id = data["user_id"]
        head_count = data["head_count"]
        total_amount = data["flight_total"]
        passengers = data["passengers"]
        flights = data["flights"]
        booking_date_str = data["booking_date"]
        end_date_str = data["end_date"]
        source_place = data["source_place"]
        package_startdate_str = data["src_to_first_arrival_time"]
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
        package_startdate = datetime.strptime(package_startdate_str, "%Y-%m-%dT%H:%M:%S")

        package = TourPackage.objects.get(package_id=package_id)
        user = TripPackageUsers.objects.get(user_id=user_id)
        booking = TripPackageBookings.objects.create(
            package=package,
            user=user,
            total_amount=(total_amount+package.price)*head_count,
            status="confirmed",
            booking_date=booking_date,
            end_date=end_date,
            package_startdate=package_startdate,
            source_place=source_place
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
            logger.info(f"Sending flight booking request: {flight_request}")
            flight_response = call_flight_service(flight_request, f"{url}/booking/book")
            logger.info(f"Received flight booking response: {flight_response}")

            # BookingTickets.objects.create(
            #         booking=booking,
            #         flight_booking_id=flight_response.get("booking_id"),
            #         source_city=flight["source_city"],
            #         destination_city=flight["destination_city"],
            #         arrival_time=datetime.strptime(flight["arrival_time"], "%Y-%m-%dT%H:%M:%S"),
            #         departure_time=datetime.strptime(flight["departure_time"], "%Y-%m-%dT%H:%M:%S")
            #     )
            arrival_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["arrival_time"] else "%Y-%m-%d %H:%M:%S"
            departure_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["departure_time"] else "%Y-%m-%d %H:%M:%S"

            BookingTickets.objects.create(
                booking=booking,
                flight_booking_id=flight_response.get("booking_id"),
                source_city=flight.get("source_city", ""),
                destination_city=flight.get("destination_city", ""),
                arrival_time=timezone.make_aware(datetime.strptime(flight["arrival_time"], arrival_format)),
                departure_time=timezone.make_aware(datetime.strptime(flight["departure_time"], departure_format))
            )
        return Response({
            "message": "Booking and flight tickets successfully stored.",
            "booking_id": booking.booking_id
        }, status=200)

    except Exception as e:
        logger.exception("Error occurred in create_booking")
        return Response({"error": str(e)}, status=400)
    
@api_view(['POST'])
def fetch_ticket_details(request):
    logger.info(f"Received fetch_ticket_details request payload: {request.data}")
    tickets = request.data.get("tickets", [])
    if not tickets:
        return Response({"error": "No tickets provided"}, status=status.HTTP_400_BAD_REQUEST)

    results = []

    # Paths to your certificate, key, and optional CA
    cert_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/django.crt"
    key_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/django.key"
    # ca_path = "D:/SEM-9/SOA Lab/Tour_Packages/Tour_Planners/tour_package/ssl/ca.crt"  # Optional for verification

    for ticket in tickets:
        booking_id = ticket.get("flight_booking_id")
        if booking_id:
            api_url = f"{url}/booking/{booking_id}"
            logger.info(f"Fetching ticket details from: {api_url}")
            try:
                # Include client cert and key
                response = requests.get(
                    api_url,
                    timeout=10,
                    cert=(cert_path, key_path),
                    verify=False  # Change to verify=ca_path in production
                )
                logger.info(f"Response from ticket service for {booking_id}: {response.status_code} - {response.text}")
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    results.append({"booking_id": booking_id, "error": "Failed to fetch data"})
            except requests.RequestException as e:
                logger.exception(f"Error fetching ticket details for {booking_id}")
                results.append({"booking_id": booking_id, "error": str(e)})

    return Response({"results": results}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user_bookings(request, user_id):
    logger.info(f"Fetching bookings for user_id: {user_id}")
    bookings = TripPackageBookings.objects.filter(user_id=user_id).select_related('package').prefetch_related('trippackagepassengers_set', 'bookingtickets_set')
    serializer = BookingSerializer(bookings, many=True)
    logger.info(f"Found {len(serializer.data)} bookings for user_id: {user_id}")
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def cancel_flights(request):
    try:
        data = request.data
        logger.info(f"Received cancel_flights request payload: {data}")

        # Extract flight_booking_ids
        booking_ids = {p['booking_id'] for p in data.get('affected_passengers', []) if p.get('booking_id')}
        if not booking_ids:
            logger.warning("No booking_ids provided in request")
            return Response({"error": "affected_passengers with booking_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Update ticket statuses
        updated_count = BookingTickets.objects.filter(flight_booking_id__in=booking_ids).update(flight_status="cancelled")
        logger.info(f"Updated {updated_count} tickets to cancelled for flight_booking_ids: {booking_ids}")

        # Collect distinct user emails
        emails = []
        for ticket in BookingTickets.objects.filter(flight_booking_id__in=booking_ids).select_related("booking__user"):
            user_email = ticket.booking.user.email
            if user_email and user_email not in emails:
                emails.append(user_email)
                logger.debug(f"Collected email {user_email} for flight_booking_id {ticket.flight_booking_id}")

        if not emails:
            logger.warning(f"No user emails found for booking_ids: {booking_ids}")
            return Response({"error": "No valid emails found"}, status=status.HTTP_404_NOT_FOUND)

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": email_api_key
        }

        results = []
        for email in emails:
            mail_payload = {
                "from": "fliptrip1025@gmail.com",  # constant sender
                "to": email,                       # single string (not list)
                "subject": data.get("subject", "Trip Update"),
                "body": data.get("body", "Your trip details have been updated.")
            }
            logger.info(f"Sending mail payload: {mail_payload}")

            response = requests.post(
                f"{email_service_url}/service/send_email",
                json=mail_payload,
                headers=headers,
                timeout=10
            )
            results.append({"email": email, "status": response.status_code})
            logger.info(f"Email sent to {email} with status {response.status_code}")

        return Response(
            {"message": f"Emails sent to {len(emails)} users", "results": results},
            status=status.HTTP_200_OK
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while calling email service: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.exception("Unexpected error in proxy_send_email")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def cancel_booking(request):
    logger.info(f"Received cancel_booking request payload: {request.data}")
    booking_id = request.data.get("booking_id")
    if not booking_id:
        return Response({"error": "booking_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        booking = TripPackageBookings.objects.get(booking_id=booking_id)
        booking.status = "cancelled"
        booking.save()
        flight_ids = list(
            BookingTickets.objects.filter(booking_id=booking_id)
            .values_list("flight_booking_id", flat=True)
        )
        flight_request = {"flight_booking_ids": flight_ids}
        logger.info(f"Sending cancel flight request: {flight_request}")
        flight_response = call_flight_service(flight_request, f"{url}/flights/bookings/cancel")
        logger.info(f"Cancel flight response: {flight_response}")

        if flight_response.get("status") == 200 or flight_response.get("success") is True:
            BookingTickets.objects.filter(flight_booking_id__in=flight_ids).update(flight_status="cancelled")
            logger.info(f"Flight tickets {flight_ids} marked as cancelled in DB")

        return Response({
            "message": "Booking and flight tickets cancelled successfully",
            "flight_response": flight_response
        })
    
    except TripPackageBookings.DoesNotExist:
        logger.warning(f"Booking {booking_id} not found")
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Error occurred in cancel_booking for booking_id {booking_id}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_booking(request):
    logger.info(f"Received update_booking request payload: {request.data}")
    try:
        data = request.data
        booking_id = data["booking_id"]  
        head_count = data["head_count"]
        passengers = data["passengers"]
        flights = data["flights"]

        booking = TripPackageBookings.objects.get(booking_id=booking_id)
        canceled_flight_ids = []

        for flight in flights:
            existing_tickets = BookingTickets.objects.filter(
                booking=booking,
                source_city=flight["source_city"],
                destination_city=flight["destination_city"]
            )
            create_new_ticket = False

            if existing_tickets.exists():
                for ticket in existing_tickets:
                    arrival_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["arrival_time"] else "%Y-%m-%d %H:%M:%S"
                    departure_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["departure_time"] else "%Y-%m-%d %H:%M:%S"

                    flight_arrival = timezone.make_aware(datetime.strptime(flight["arrival_time"], arrival_format))
                    flight_departure = timezone.make_aware(datetime.strptime(flight["departure_time"], departure_format))

                    if ticket.flight_status == "cancelled" or ticket.arrival_time != flight_arrival or ticket.departure_time != flight_departure:
                        canceled_flight_ids.append(ticket.flight_booking_id)
                        create_new_ticket = True
                        ticket.delete()
            else:
                create_new_ticket = True

            if create_new_ticket:
                flight_request = {
                    "flight_id": flight["flight_id"],
                    "travel_date": flight["departure_time"].split(" ")[0],
                    "seats_required": head_count,
                    "passenger_details": passengers
                }
                logger.info(f"Sending flight booking request: {flight_request}")
                flight_response = call_flight_service(flight_request, f"{url}/booking/book")
                logger.info(f"Flight booking response: {flight_response}")

                arrival_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["arrival_time"] else "%Y-%m-%d %H:%M:%S"
                departure_format = "%Y-%m-%dT%H:%M:%S" if "T" in flight["departure_time"] else "%Y-%m-%d %H:%M:%S"

                BookingTickets.objects.create(
                booking=booking,
                flight_booking_id=flight_response.get("booking_id"),
                flight_status=flight_response.get("status", "confirmed"),
                source_city=flight["source_city"],
                destination_city=flight["destination_city"],
                arrival_time=timezone.make_aware(datetime.strptime(flight["arrival_time"], arrival_format)),
                departure_time=timezone.make_aware(datetime.strptime(flight["departure_time"], departure_format))
                )
        if canceled_flight_ids:
            flight_request = {"flight_booking_ids": canceled_flight_ids}
            logger.info(f"Sending cancel flight request: {flight_request}")
            flight_response = call_flight_service(flight_request, f"{url}/flights/bookings/cancel")
            logger.info(f"Cancel flight response: {flight_response}")

            if flight_response.get("status") == 200 or flight_response.get("success") is True:
                BookingTickets.objects.filter(flight_booking_id__in=canceled_flight_ids).update(flight_status="cancelled")
                logger.info(f"Flight tickets {canceled_flight_ids} marked as cancelled in DB")

        return Response({
            "message": "Flight tickets processed successfully.",
            "booking_id": booking.booking_id,
            "canceled_flights": canceled_flight_ids
        }, status=200)

    except Exception as e:
        logger.exception(f"Error occurred in update_booking for booking_id {request.data.get('booking_id')}")
        return Response({"error": str(e)}, status=400)
    
@api_view(['POST'])
def proxy_check_otp(request):
    try:
        # Use the POST data sent from frontend or override/merge with secretKey
        payload = request.data.copy()  # get frontend data
        payload["secretKey"] = phone_api_key  # ensure secretKey is included

        # Call the HTTP API
        response = requests.post(
            f"{phone_service_url}/api/check-otp-availability",
            json=payload,
            timeout=10
        )

        # Forward the API response as-is
        return Response(response.json(), status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
def proxy_send_email(request):
    try:
        mail_payload = request.data  # take payload from frontend

        # Add API key securely in backend
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": email_api_key
        }

        # Forward to email service
        response = requests.post(
            f"{email_service_url}/service/send_email",
            json=mail_payload,
            headers=headers,
            timeout=10
        )

        return Response(response.json(), status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
def proxy_email_verification(request):
    """
    Proxy endpoint for verifying email credentials.
    Forwards request payload to external email service securely.
    """
    logger.info("Received email verification request payload: %s", request.data)

    email = request.data.get("email")
    password = request.data.get("password")
    token_expiry_minutes = request.data.get("token_expiry_minutes", 60)

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Forward request to external service
        response = requests.post(
            f"{email_service_url}/service/pure_auth",
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": email_api_key
            },
            json={
                "email": email,
                "password": password,
                "token_expiry_minutes": token_expiry_minutes
            },
            timeout=15
        )
        logger.info("External email service responded with status %s", response.status_code)

        try:
            data = response.json()
        except Exception:
            logger.error("Failed to decode JSON response from email service")
            return Response({"error": "Invalid response from email service"}, status=status.HTTP_502_BAD_GATEWAY)

        if response.ok:
            return Response(data, status=response.status_code)
        else:
            return Response(data, status=response.status_code)

    except requests.RequestException as e:
        logger.error("Error contacting email service: %s", str(e))
        return Response({"error": "Failed to reach email service"}, status=status.HTTP_502_BAD_GATEWAY)