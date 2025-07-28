# views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import TourPackage, PackageCity
from .serializers import TourPackageSerializer
from django.db.models import Sum, F

@api_view(['POST'])
def filter_packages_by_city_price(request):
    budget = request.data.get('budget')
    if budget is None:
        return Response({'error': 'Budget is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        budget = float(budget)
    except ValueError:
        return Response({'error': 'Invalid budget value'}, status=status.HTTP_400_BAD_REQUEST)
    
    matching_packages = []
    packages = TourPackage.objects.all()
    for package in packages:
        package_cities = PackageCity.objects.filter(package=package).select_related('city')
        total_city_price = sum(
            (pc.city.city_price or 0) for pc in package_cities
        )
        if total_city_price <= budget:
            matching_packages.append(package)
    print(matching_packages)
    #serializer = TourPackageSerializer(matching_packages, many=True)
    #return Response(serializer.data, status=status.HTTP_200_OK)
