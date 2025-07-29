from django.urls import path
from .views import *

urlpatterns = [
    path('filter_package', filter_package, name='filter_package'),  
]
