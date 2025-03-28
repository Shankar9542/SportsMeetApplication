from django.urls import path
from . import views
from .views import *
from django.views.generic import TemplateView


app_name='SportMeetApp'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('api/register-user/', RegisterUserView.as_view(), name='register-user'),
    path('register/', register_view, name='register'),
    path('register-venue/', register_venue, name='register-venue'),
    path('register/venue/add/<int:user_id>/', register_venue_add, name='register-add-venue'),
    path('register-owner/',VenueOwnerRegisterView.as_view(),name='register-owner'),
    path('registration_success/',registration_success, name='registration_success'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', views.user_login, name='login'),
    path('logout/', logout_view, name='logout'),
    # path('admin-logout/', admin_logout, name='admin-logout'),
    path('approval/', views.approval_page, name='approval'),
    path('api/venues/', VenueListView.as_view(), name='venue-list'),
    path('allvenues/', VenueAllListView.as_view(), name='allvenue-list'),
    path('api/sporttypes/', SporttypeListView.as_view(), name='sporttype-list'),
    path("api/search-venues/", search_venues, name="search_venues"),
    path("search-results/", search_results, name="search_results"),
    path('sports_venue', sports_venue, name='sports-venue'),
    path('venues/<int:venue_id>/', VenueDetailView.as_view(), name='venue-detail'),
    path('booking-view/<int:venue_id>/', booking_view, name='booking-view'),
    path('venue-owner-booking-view/', venue_owner_booking_view, name='venue-owner-booking-view'),
    path('venue-owner-booking-view/<int:venue_id>/', venue_owner_booking_view, name='venue-owner-booking-view-with-id'),
    path('api/get_bookings/', GetBookingsView.as_view(), name='get_bookings'),
    path('api/bookings/', BookingCreateAPIView.as_view(), name='bookings'),
    path('api/password-reset/', send_password_reset_email, name='password-reset'),
    path("api/password-reset-confirm/<uidb64>/<token>/", reset_password_confirm, name="password_reset_confirm"),
    path('password_reset/', password_reset_view, name='password_reset'),
    path('reset-password/<uidb64>/<token>/', password_reset_confirm_view, name='password-reset-form'),
    path('success/', success_page, name='success'),
    path('dashboard-success/', dashboard_success_page, name='dashboard-success'),
    path('venues/<int:venue_id>/submit_review/', ReviewListCreateView.as_view(), name='submit_review'),
    path('test-emails/', test_booking_emails),
    path('api/location-suggestions/', location_suggestions, name='location-suggestions'),
    path('customer_chat/', views.customer_chat, name='customer_chat'),
    path('admin_chat/', views.admin_chat, name='admin_chat'),
    path('get_messages/', views.get_messages, name='get_messages'),
    path('send_message/', views.send_message, name='send_message'),
    path('get_messaged_customers/', views.get_messaged_customers, name='get_messaged_customers'),
    path('customer-dashboard/',customer_dashboard,name="customer-dashboard"),
    path('venue/<int:venue_id>/policy/', venue_policy_view, name='venue_policy'),
    path('sports/<int:sport_id>/venues/', views.venues_by_sport, name='venues_by_sport'),
    # path('api/validate_coupon/', ValidateCouponAPIView.as_view(), name='validate_coupon'),
    
    path('dashboard/', views.dashboard, name='dashboard'),

    # API Endpoints
    path('get_total_revenue/', views.get_total_revenue, name='get_total_revenue'),
    path('get_total_users/', views.get_total_users, name='get_total_users'),
    path('get_total_venues/', views.get_total_venues, name='get_total_venues'),
    path('get_daywise_bookings/<int:venue_id>/<str:month>/', views.get_daywise_bookings, name='get_daywise_bookings'),
    path('get_weekwise_revenue/<int:venue_id>/<str:month>/', views.get_weekwise_revenue, name='get_weekwise_revenue'),
  
 
 
    path("venue/<int:venue_id>/location/", venue_location, name="venue_location"),
    path('venue/<int:venue_id>/save-location/', views.save_venue_location, name='save_venue_location'),
    path('nearby-venues/', nearby_venues, name='nearby-venues'),
    
    path('dashboard-reports/', reports_dashboard, name='dashboard-reports'),
]
    
    

    
    

    

    
