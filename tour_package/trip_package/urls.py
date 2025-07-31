from django.urls import path
from .views import *

urlpatterns = [
    path('filter_package', filter_package, name='filter_package'), 
    path('start_flight_options', start_flight_options, name='start_flight_options'),
    path('generate_flight_plan', generate_flight_plan, name='generate_flight_plan'),
    path('end_flight_options', end_flight_options, name='end_flight_options'),
    path('register_user', register_user, name='register_user'),
    path('login_user', login_user, name='login_user'),
    path('get_user_details', get_user_details, name='get_user_details'),
    path('update_user_details', update_user_details, name='update_user_details'),
    path('change_password', change_password,name='change_password')
]
