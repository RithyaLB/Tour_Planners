from django.urls import path
from .views import *

urlpatterns = [
    path('filter_package', filter_package, name='filter_package'), 
    path('start_flight_options', start_flight_options, name='start_flight_options'),
    path('generate_flight_plan', generate_flight_plan, name='generate_flight_plan'),
    path('end_flight_options', end_flight_options, name='end_flight_options'),
    path('create_booking', create_booking, name='create_booking'),
    path('register_user', register_user, name='register_user'),
    path('login_user', login_user, name='login_user'),
    path('get_user_details', get_user_details, name='get_user_details'),
    path('update_user_details', update_user_details, name='update_user_details'),
    path('change_password', change_password, name='change_password'),
    path('view_bookings/<int:user_id>/', get_user_bookings, name='view_bookings'),
    path('fetch_ticket_details', fetch_ticket_details, name='fetch_ticket_details'),
    path('cancel_flights', cancel_flights, name='cancel_flights'),
    path('cancel_booking', cancel_booking, name='cancel_booking'),
    path('update_booking', update_booking, name='update_booking'),
    path("proxy_check_otp", proxy_check_otp, name="proxy_check_otp"),
    path("proxy_send_email", proxy_send_email, name="proxy_send_email"),
    path("proxy_email_verification", proxy_email_verification, name="proxy_email_verification"),
]
