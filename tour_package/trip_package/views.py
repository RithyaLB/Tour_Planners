from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from datetime import datetime,timedelta

def remove_duplicates(city_list):
    unique_set = set()
    unique_cities = []
    for city in city_list:
        key = (city['source'], city['start_date'], city['destination'])
        if key not in unique_set:
            unique_set.add(key)
            unique_cities.append(city)
    return unique_cities

def external_start_flight(packages,starting_place,start_date):
    all_startingplace = []
    for package in packages:
            package_cities = PackageCity.objects.filter(package=package).order_by('sequence').first()
            if package_cities:
                if starting_place != package_cities.city.city_name:
                    start = {
                        "start_date": start_date.strftime("%Y-%m-%d %H:%M"),
                        "source": starting_place,
                        "destination": package_cities.city.city_name,
                        "limit": 5
                    }
                    all_startingplace.append(start)
    return all_startingplace

def external_end_flight(packages,starting_place,start_date):
    all_endingplace = []
    for package in packages:
            package_cities = PackageCity.objects.filter(package=package).order_by('-sequence').first()
            if package_cities:
                if starting_place != package_cities.city.city_name:
                    spots = Spot.objects.filter(city=package_cities.city).order_by('-day_no')
                    if not spots.exists():
                        continue 
                    latest_spot = spots.first()
                    day_no = latest_spot.day_no or 0
                    timing = latest_spot.timing or datetime.strptime("09:00", "%H:%M").time() 
                    duration_hours = float(latest_spot.duration or 0)
                    target_date = start_date + timedelta(days=day_no)
                    timing_datetime = datetime.combine(target_date, timing)
                    final_return_time = timing_datetime + timedelta(hours=duration_hours)
                    start = {
                        "start_date": final_return_time.strftime("%Y-%m-%d %H:%M"),
                        "source": package_cities.city.city_name,
                        "destination": starting_place,
                        "limit": 5,
                    }
                    all_endingplace.append(start)
    return all_endingplace

@api_view(['POST'])
def filter_package(request):
    budget = request.data.get('budget')
    start_date = request.data.get('start_date')
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    starting_place = request.data.get('starting_place')
    if budget and start_date and starting_place:
        packages = TourPackage.objects.filter(price__lte=budget)
        all_startingplace = external_start_flight(packages,starting_place,start_date)
        unique_startingplace = remove_duplicates(all_startingplace)
        print(unique_startingplace)

        all_cities = []
        for package in packages:
            package_cities = list(PackageCity.objects.filter(package=package).order_by('sequence'))
            current_date = start_date
            for i in range(len(package_cities) - 1):  
                current_pc = package_cities[i]
                next_pc = package_cities[i + 1]
                city = current_pc.city
                stay_duration = city.stay_duration or 0
                city_start_date = current_date
                city_end_date = city_start_date + timedelta(days=stay_duration)
                city_dict = {
                    "start_date": start_date.strftime("%Y-%m-%d %H:%M"),
                    "source": city.city_name,
                    "destination": next_pc.city.city_name,
                    "limit" : 1,
                }
                all_cities.append(city_dict)
                current_date = city_end_date
        unique_cities = remove_duplicates(all_cities)

        all_endingplace = external_end_flight(packages,starting_place,start_date)
        unique_endingplace = remove_duplicates(all_endingplace)
        print(unique_endingplace)

        return Response(unique_startingplace, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Budget is required'}, status=status.HTTP_400_BAD_REQUEST)