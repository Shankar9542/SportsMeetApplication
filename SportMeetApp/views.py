
from datetime import date
import json
from django.utils import timezone
import re
from django.urls import reverse
from django.views import View
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status,permissions
from rest_framework.decorators import api_view,permission_classes
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomerProfile, VenueOwnerProfile
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User,Group
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from django.db.models import Q
import requests
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date
from .utils.email_utils import send_booking_confirmation_email, send_booking_reminder_email
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from.forms import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from .utils.geo_utils import haversine_distance

def test_booking_emails(request):
    user_email = 'avinashnukathoti357@gmail.com'
    user_name = 'Avinash'
    venue_name = 'Grand Palace'

    # Send both emails for testing purposes
    send_booking_confirmation_email(user_email, user_name, venue_name)
    send_booking_reminder_email(user_email, user_name, venue_name)

    return JsonResponse({'status': 'Test emails sent successfully'})

def home(request):
    banner = Banner.objects.first()
    venue = Venue.objects.all()
    sports=Sporttype.objects.all()
    
    context = {
        'banner_image': banner.bannerimage.url if banner and banner.bannerimage else None,
        'sports': list(sports),
        'venue': venue
    }
    return render(request, "index.html", context)



def approval_page(request):
    return render(request, "approval.html")

# def validate_password(password):
#     """
#     Validate password to ensure it meets the following criteria:
#     - At least 8 characters long
#     - Contains at least one uppercase letter
#     - Contains at least one digit
#     - Contains at least one special character
#     """
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."

#     if not re.search(r'[A-Z]', password):
#         return False, "Password must contain at least one uppercase letter."

#     if not re.search(r'[0-9]', password):
#         return False, "Password must contain at least one digit."

#     if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
#         return False, "Password must contain at least one special character."

#     return True, "Password is valid."

def sports_venue(request):
    return render(request, "sportspage.html")

def sports(request):
    return render(request,'sports.html')



class VerifyEmailView(APIView):
    def get(self, request, token):
        try:
            # Find the token in the database
            token_obj = EmailVerificationToken.objects.get(token=token)
            user = token_obj.user

            # Optional: Check if the user is already verified
            if user.is_active:
                return Response({"message": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

            # Activate the user
            user.is_active = True
            user.save()

            # Delete the token (it's no longer needed)
            token_obj.delete()

            # Optional: Set a "verified" flag on the user profile (if you have one)
            # if hasattr(user, 'profile'):
            #     user.profile.email_verified = True
            #     user.profile.save()

            return redirect(reverse('SportMeetApp:login') + '?verified=1')

        except EmailVerificationToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
      
class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                'success': 'Registration successful! Please check your email to verify your account.',
                'redirect_url': request.build_absolute_uri(reverse('SportMeetApp:registration_success'))
            }, status=status.HTTP_201_CREATED)
        else:
            # Return field-specific errors in a consistent format
            errors = {}
            for field, error_list in serializer.errors.items():
                errors[field] = error_list
            return JsonResponse({
                'error': errors
            }, status=status.HTTP_400_BAD_REQUEST)


  
def register_view(request):
    return render(request, "register.html")

def register_venue(request):
    return render(request, "register_venue.html")
    
def registration_success(request):
    return render(request, "register_success.html")


class VenueOwnerRegisterView(generics.CreateAPIView):
    serializer_class = VenueOwnerRegisterSerializer
    

    def create(self, request, *args, **kwargs):
        # import pdb
        # pdb.set_trace()
        """Handles venue owner registration and redirects with user ID."""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()  # Save user and get the instance
            messages.success(request, "Registration successful! Please add your venue details.")

            # Correct URL redirection
            return JsonResponse({
            'success': 'Registration successful! Please add your venue details.',
            'redirect_url': f'/register/venue/add/{user.id}/'
            })
        else:
            # Return field-specific errors in a consistent format
            errors = {}
            for field, error_list in serializer.errors.items():
                errors[field] = error_list
            return JsonResponse({
                'error': errors
            }, status=status.HTTP_400_BAD_REQUEST)

 





def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')  # Get email from the form
        password = request.POST.get('password')  # Get password from the form

        # Check if a user with the provided email exists
        try:
            user = User.objects.get(email=email)  # Fetch user by email
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
            return redirect("SportMeetApp:login")  # Redirect back to the login page

        # Authenticate the user
        user = authenticate(request, username=user.username, password=password)

        if user is not None:
            # Check if the user is a venue owner
            try:
                venue_owner_profile = VenueOwnerProfile.objects.get(user=user)
                if not venue_owner_profile.is_approved:
                    # If not approved, show a message
                    messages.info(request, "Your account is pending approval.")
                    return redirect("SportMeetApp:approval")  # Redirect to the approval page
                else:
                    # If approved, redirect to the dashboard
                    login(request, user)
                    group = Group.objects.get(name='owner')
                    user.groups.add(group)
                    return redirect(reverse('admin:index'))  # Redirect to the dashboard page
            except VenueOwnerProfile.DoesNotExist:
                # If the user is not a venue owner, check if they are a customer
                try:
                    customer_profile = CustomerProfile.objects.get(user=user)
                    # If the user is a customer, redirect to the home page
                    login(request, user)
                    group = Group.objects.get(name='customer')
                    user.groups.add(group)
                    return redirect("SportMeetApp:home")  # Redirect to the home page
                except CustomerProfile.DoesNotExist:
                    # If the user is neither a venue owner nor a customer, handle accordingly
                    messages.error(request, "User profile not found.")
                    return redirect("SportMeetApp:login")  # Redirect back to the login page
        else:
            messages.error(request, "Invalid credentials.")
            return redirect("SportMeetApp:login")  # Redirect back to the login page

    return render(request, "login.html")


def customer_dashboard(request):
    return redirect(reverse('admin:index'))


def logout_view(request):
  
    user = request.user  # Get the logged-in user
    logout(request)  # Logout the user

    # Redirect based on user type
    if user.is_superuser:
        return redirect('/admin/')  # Superuser -> Admin Login
    elif user.groups.filter(name='owner').exists():  # Venue Owner
        return redirect('/login/')  # Venue Owner -> Login Page
    else:  # Customer
        return redirect('/home/')



class VenueListView(APIView):
    def get(self, request):
        # Filter venues where the associated VenueOwnerProfile is approved
        venues = Venue.objects.filter(owner__is_approved=True)[:6]
        serializer = VenueSerializer(venues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class VenueAllListView(APIView):
    def get(self, request):
        # Filter venues where the associated VenueOwnerProfile is approved
        venues = Venue.objects.filter(owner__is_approved=True)
        serializer = VenueSerializer(venues, many=True)
        
        context = {
            'venues': serializer.data,
        }
        return render(request, 'venues.html', context)
        
    



class VenueDetailView(APIView):
    def get(self, request, venue_id):
        venue = get_object_or_404(Venue.objects.prefetch_related('images', 'courts', 'ratings'), id=venue_id)
        serializer = VenueSerializer(venue)

        venue_images = venue.images.all()
        venue_courts = venue.courts.values('sport__id', 'sport__name', 'sport__image').distinct()
        

        # Fetch reviews directly
        reviews = venue.ratings.all()

        context = {
            'venue': venue,
            'venue_images': venue_images,
            'venue_courts': venue_courts,
            'reviews': reviews,  # Pass reviews separately
        }
        return render(request, 'sportspage.html', context)
    
def venues_by_sport(request, sport_id):
    # Get the sport object or return a 404 if not found
    sport = get_object_or_404(Sporttype, id=sport_id)
    
    # Filter venues that have courts related to the selected sport
    venues = Venue.objects.filter(courts__sport=sport, owner__is_approved=True).distinct()
    
    # Pass the sport and venues to the template
    context = {
        'sport': sport,
        'venues': venues,
    }
    
    return render(request, 'venues_by_sport.html', context)
        
class SporttypeListView(APIView):
    def get(self, request):
        sporttypes = Sporttype.objects.all() # Get the first 6 sport types
        serializer = SporttypeSerializer(sporttypes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



@api_view(["GET"])
def search_venues(request):
    """
    Search venues based on a single location input (city, area, or address).
    Also filters by sport type and date if provided.
    """
    location = request.GET.get("location", "").strip()  # Single location field
    sporttype = request.GET.get("sporttype", "").strip()
    date = request.GET.get("date", "").strip()  # Expected format: YYYY-MM-DD

    venues = Venue.objects.filter(owner__is_approved=True)

    # Filter by location (matches city, area, or address)
    if location:
        venues = venues.filter(
            Q(city__icontains=location) |
            Q(area__icontains=location) |
            Q(address__icontains=location)
        )

    # Filter by sport type (linked to Court model via sports relationship)
    if sporttype:
        venues = venues.filter(courts__sport__name__icontains=sporttype)

    # Filter by date
    if date:
        try:
            search_date = datetime.strptime(date, "%Y-%m-%d").date()
            venues = venues.filter(start_date__lte=search_date, end_date__gte=search_date)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

    venues = venues.distinct()

    serializer = VenueSerializer(venues, many=True)
    return Response(serializer.data, status=200)



def search_results(request):
    """
    Fetch search parameters and call the API to get search results.
    Handles location input which could be city, area, or address.
    """
    location = request.GET.get("location", "").strip()  # Single location field
    sporttype = request.GET.get("sporttype", "").strip()
    date = request.GET.get("date", "").strip()
    base_url = request.build_absolute_uri('/').strip('/')

    # Build API URL with location (can match against city, area, or address on the API side)
    api_url = f"{base_url}/api/search-venues/?sporttype={sporttype}&date={date}&location={location}"
   

    # Append location if provided
    if location:
        api_url += f"&location={location}"

   

    try:
        response = requests.get(api_url)
        results = response.json() if response.status_code == 200 else []
    except Exception as e:
        results = {"error": "Could not fetch results."}

    return render(request, "search_result.html", {"results": results})



@api_view(['GET'])
def location_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return Response([])

    # Query distinct areas and cities matching the query
    venues = Venue.objects.filter(
        Q(area__icontains=query) | Q(city__icontains=query)
    ).values_list('area', 'city').distinct()

    # Combine area & city into one string per venue
    suggestions = []
    for area, city in venues:
        if area and city:
            suggestions.append(f"{area}, {city}")
        elif area:
            suggestions.append(area)
        elif city:
            suggestions.append(city)

    # Remove duplicates (in case same area-city pair appears more than once)
    suggestions = list(set(suggestions))

    return Response(suggestions)


def success_page(request):
    return render(request, "success.html")
def dashboard_success_page(request):
    return render(request, "dashboard_sucess.html")

    

@api_view(["POST"])
def send_password_reset_email(request):
    email = request.data.get("email")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = request.build_absolute_uri(reverse("SportMeetApp:password_reset_confirm", args=[uid, token]))

    # Send Email
    send_mail(
        "Password Reset Request",
        f"Click the link to reset your password: {reset_url}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    return Response({"success": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)

@api_view(["GET", "POST"])
def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

    # Render the HTML form when accessed via GET
    if request.method == "GET":
        return render(request, "password_reset_confirm.html", {"uidb64": uidb64, "token": token})

    # Handle password reset submission via POST
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not new_password or not confirm_password:
        return Response({"error": "Both password fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    # Optional: Check password strength
    if len(new_password) < 6:
        return Response({"error": "Password must be at least 6 characters long."}, status=status.HTTP_400_BAD_REQUEST)

    user.password = make_password(new_password)
    user.save()

    return Response({"success": "Password has been reset successfully."}, status=status.HTTP_200_OK)

def password_reset_view(request):
    return render(request, "password_reset.html")

def password_reset_confirm_view(request, uidb64, token):
    """Render password reset confirmation page with UID and token."""
    context = {"uidb64": uidb64, "token": token}
    return render(request, "password_reset_confirm.html", context)



 
class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        venue_id = self.kwargs.get("venue_id")
        return Rating.objects.filter(venue_id=venue_id)

    def perform_create(self, serializer):
        venue_id = self.kwargs.get("venue_id")
        venue = get_object_or_404(Venue, id=venue_id)
        customer = get_object_or_404(CustomerProfile, user=self.request.user)  # Get the customer profile
        serializer.save(customer=customer, venue=venue)  # Save the customer profile
        


@login_required
def customer_chat(request):
    admin_user = User.objects.filter(is_superuser=True).first()  # Assuming one admin
    return render(request, 'customer_chat.html', {'admin_user': admin_user})


@login_required
def admin_chat(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    customers = User.objects.filter(is_superuser=False)  # Non-admin users
    return render(request, 'admin_chat.html', {'customers': customers})





@csrf_exempt
@login_required
def get_messages(request):
    user = request.user

    if user.is_superuser:
        # Admin gets messages for a selected customer (keep this logic)
        other_user_id = request.GET.get('other_user_id')
        other_user = get_object_or_404(User, id=other_user_id)
    else:
        # Customer gets messages only with the admin
        other_user = User.objects.filter(is_superuser=True).first()
        if not other_user:
            return JsonResponse({'error': 'Admin not found'}, status=400)

    messages = ChatMessage.objects.filter(
        (models.Q(sender=user) & models.Q(receiver=other_user)) |
        (models.Q(sender=other_user) & models.Q(receiver=user))
    ).order_by('timestamp')

    data = [
        {
            'sender': msg.sender.username,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in messages
    ]
    return JsonResponse(data, safe=False)



@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        sender = request.user
        
        # Determine the receiver based on the user type
        if sender.is_superuser:
            # Admin sends message to a selected customer
            receiver_id = request.POST.get('receiver_id')
            if not receiver_id:
                return JsonResponse({'error': 'Receiver ID is required for admin'}, status=400)
            receiver = get_object_or_404(User, id=receiver_id)
        else:
            # Customer sends message to the admin
            receiver = User.objects.filter(is_superuser=True).first()
            if not receiver:
                return JsonResponse({'error': 'Admin not found'}, status=400)

        message = request.POST.get('message')
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        ChatMessage.objects.create(sender=sender, receiver=receiver, message=message)
        return JsonResponse({'status': 'Message sent'})
    
    
    
@login_required
def get_messaged_customers(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Get unique customers who have exchanged messages with the admin
    customer_ids = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).values_list('sender_id', 'receiver_id').distinct()

    # Flatten the list and exclude the admin's ID
    unique_ids = set()
    for sender_id, receiver_id in customer_ids:
        if sender_id != request.user.id:
            unique_ids.add(sender_id)
        if receiver_id != request.user.id:
            unique_ids.add(receiver_id)

    # Fetch customer details
    customers = User.objects.filter(id__in=unique_ids, is_superuser=False)
    data = [{'id': customer.id, 'username': customer.username} for customer in customers]

    return JsonResponse(data, safe=False)








@login_required
def booking_view(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)
    discount = Discount.objects.filter(venue=venue).first()

    # Handle selected sport (filtering courts)
    selected_sport_id = request.GET.get('sport_id')
    if selected_sport_id:
        try:
            selected_sport_id = int(selected_sport_id)
        except (ValueError, TypeError):
            selected_sport_id = None

    # Fetch courts, optionally filtering by sport
    courts_query = Court.objects.filter(venue=venue).select_related('sport')
    if selected_sport_id:
        courts_query = courts_query.filter(sport_id=selected_sport_id)

    # Order courts by court_number
    courts = courts_query.order_by('court_number')

    # Fetch distinct sports available at the venue (for dropdown filter)
    distinct_sports = Sporttype.objects.filter(courts__venue=venue).distinct()

    # Collect and deduplicate all available time slots across all courts
    time_slots = set()
    for court in courts:
        slots = court.generate_time_slots()
        for start, _ in slots:
            time_slots.add(start.strftime('%I:%M %p'))  # Format as '06:00 AM'

    # Convert to sorted list using proper 24-hour time conversion
    def convert_to_24hr(time_str):
        return datetime.strptime(time_str, "%I:%M %p")

    time_slots = sorted(time_slots, key=convert_to_24hr)

    # Handle selected date (default to today, ensure valid date)
    selected_date_str = request.GET.get('date', date.today().isoformat())
    selected_date = parse_date(selected_date_str) or date.today()

    # Fetch bookings for the selected date
    bookings = Booking.objects.filter(
        court__venue=venue,
        date=selected_date
    ).select_related('court')

    # Create a map of booked slots (time -> [court_numbers])
    booked_slots = {}
    for booking in bookings:
        slot_time = booking.start_time.strftime('%I:%M %p')
        if slot_time not in booked_slots:
            booked_slots[slot_time] = []
        booked_slots[slot_time].append(booking.court.court_number)

    # Convert courts to JSON-friendly data
    courts_data = [
        {
            'id': court.id,
            'court_number': court.court_number,
            'sport_id': court.sport.id,
            'sport_name': court.sport.name,
            'price': float(court.price),  # Convert Decimal to float for JSON
            'duration': court.duration
        }
    
        for court in courts
    ]
 

    context = {
        'venue': venue,
        'discount':discount.discount if discount else 0,
        'time_slots_json': json.dumps(time_slots),
        'courts_json': json.dumps(courts_data),
        'booked_slots_json': json.dumps(booked_slots),
        'distinct_sports': distinct_sports,
        'selected_date': selected_date.isoformat(),
        'selected_sport_id': selected_sport_id,
        'today': date.today().isoformat(),  # For datepicker `min`
        'max_date': venue.end_date.isoformat() if venue.end_date else None  # For datepicker `max`
    }

    return render(request, 'booking.html', context)





@login_required
@user_passes_test(lambda u: hasattr(u, 'venue_owner_profile'))
def venue_owner_booking_view(request, venue_id=None):
    # Fetch all venues owned by the venue owner
    venues = Venue.objects.filter(owner=request.user.venue_owner_profile)
   
    
    # If a specific venue is selected, use it; otherwise, use the first venue
    if venue_id:
        venue = get_object_or_404(Venue, id=venue_id, owner=request.user.venue_owner_profile)
    else:
        venue = venues.first()
        
    discount = Discount.objects.filter(venue=venue).first()

    # Handle selected sport (filtering courts)
    selected_sport_id = request.GET.get('sport_id')
    if selected_sport_id:
        try:
            selected_sport_id = int(selected_sport_id)
        except (ValueError, TypeError):
            selected_sport_id = None

    # Fetch courts, optionally filtering by sport
    courts_query = Court.objects.filter(venue=venue).select_related('sport')
    if selected_sport_id:
        courts_query = courts_query.filter(sport_id=selected_sport_id)

    # Order courts by court_number
    courts = courts_query.order_by('court_number')

    # Fetch distinct sports available at the venue (for dropdown filter)
    distinct_sports = Sporttype.objects.filter(courts__venue=venue).distinct()

    # Collect and deduplicate all available time slots across all courts
    time_slots = set()
    for court in courts:
        slots = court.generate_time_slots()
        for start, _ in slots:
            time_slots.add(start.strftime('%I:%M %p'))  # Format as '06:00 AM'

    # Convert to sorted list using proper 24-hour time conversion
    def convert_to_24hr(time_str):
        return datetime.strptime(time_str, "%I:%M %p")

    time_slots = sorted(time_slots, key=convert_to_24hr)

    # Handle selected date (default to today, ensure valid date)
    selected_date_str = request.GET.get('date', date.today().isoformat())
    selected_date = parse_date(selected_date_str) or date.today()

    # Fetch bookings for the selected date
    bookings = Booking.objects.filter(
        court__venue=venue,
        date=selected_date
    ).select_related('court')

    # Create a map of booked slots (time -> [court_numbers])
    booked_slots = {}
    for booking in bookings:
        slot_time = booking.start_time.strftime('%I:%M %p')
        if slot_time not in booked_slots:
            booked_slots[slot_time] = []
        booked_slots[slot_time].append(booking.court.court_number)

    # Convert courts to JSON-friendly data
    courts_data = [
        {
            'id': court.id,
            'court_number': court.court_number,
            'sport_id': court.sport.id,
            'sport_name': court.sport.name,
            'price': float(court.price),  # Convert Decimal to float for JSON
            'duration': court.duration
        }
        for court in courts
    ]

    context = {
        'venue': venue,
        'discount':discount.discount if discount else 0,
        'venues': venues,  # Pass all venues to the template
        'time_slots_json': json.dumps(time_slots),
        'courts_json': json.dumps(courts_data),
        'booked_slots_json': json.dumps(booked_slots),
        'distinct_sports': distinct_sports,
        'selected_date': selected_date.isoformat(),
        'selected_sport_id': selected_sport_id,
        'today': date.today().isoformat(),  # For datepicker `min`
        'max_date': venue.end_date.isoformat() if venue.end_date else None  # For datepicker `max`
    }

    return render(request, 'booking_change_form.html', context)


class GetBookingsView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the selected date and sport_id from the request
        
        # import pdb
        # pdb.set_trace()
        selected_date_str = request.query_params.get('date')
        sport_id = request.query_params.get('sport_id')
       

        # Parse the selected date
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sport_id = int(sport_id)  # or UUID(sport_id) if it's a UUID field
        except (ValueError, TypeError) as e:
            print(f"Error parsing sport_id: {e}")
            return Response({'error': 'Invalid sport_id'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all courts for the selected sport
        courts = Court.objects.filter(sport_id=sport_id).values_list('court_number', flat=True)
       

        # Fetch bookings for the selected date and sport
        bookings = Booking.objects.filter(date=selected_date,court__sport_id=sport_id, booking_status='confirmed').select_related('court')

        # Create a map of booked slots (time -> [court_numbers])
        booked_slots = {}
        for booking in bookings:
            start_time = booking.start_time
            end_time = booking.end_time
           
            # Generate all time slots between start_time and end_time
            current_time = start_time
            while current_time < end_time:
                slot_time = current_time.strftime('%I:%M %p')
                if slot_time not in booked_slots:
                    booked_slots[slot_time] = []
                booked_slots[slot_time].append(booking.court.court_number)
                current_time = (datetime.combine(selected_date, current_time) + timedelta(minutes=30)).time()

        # Return the booked slots as JSON
        return Response({'booked_slots': booked_slots}, status=status.HTTP_200_OK)





class BookingCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        mutable_data = request.data.copy()

        # Check if the user is a venue owner
        is_venue_owner = hasattr(request.user, 'venue_owner_profile')

        if is_venue_owner:
            # Venue owner is creating a booking for a customer
            if 'customer_name' in mutable_data and mutable_data['customer_name']:
                customer_name = mutable_data['customer_name']

                # Generate a temporary username
                temp_username = customer_name.lower().replace(" ", "_") 

                # Create a new User object
                user, created = User.objects.get_or_create(
                    username=temp_username, 
                    defaults={
                        "first_name": customer_name.split()[0],  
                        "last_name": " ".join(customer_name.split()[1:]) if " " in customer_name else "",
                    }
                )

                # Create a CustomerProfile if needed
                customer_profile, _ = CustomerProfile.objects.get_or_create(user=user)

                # Assign customer profile to the booking
                mutable_data['customer'] = customer_profile.id

                # Assign the venue owner to the booking
                mutable_data['venue_owner'] = request.user.venue_owner_profile.id

            else:
                return Response({'error': 'Customer information is required.'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Regular customer is creating a booking
            if request.user.is_authenticated:
                try:
                    customer_profile = CustomerProfile.objects.get(user=request.user)
                except CustomerProfile.DoesNotExist:
                    customer_profile = CustomerProfile.objects.create(user=request.user)

                # Assign customer profile to the booking
                mutable_data['customer'] = customer_profile.id

            else:
                return Response({'error': 'Authentication required for customers.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Set the booking status to confirmed
        mutable_data['booking_status'] = 'confirmed'

        # Validate and save the booking
        serializer = BookingSerializer(data=mutable_data)
        if serializer.is_valid():
            try:
                # Check for overlapping bookings
                court = Court.objects.get(id=mutable_data['court'])
                overlapping_bookings = Booking.objects.filter(
                    court=court,
                    date=mutable_data['date'],
                    start_time__lt=mutable_data['end_time'],
                    end_time__gt=mutable_data['start_time'],
                    booking_status__in=['pending', 'confirmed'],  
                ).exists()

                if overlapping_bookings:
                    return Response({'error': 'This court is already booked for the selected time slot.'}, status=status.HTTP_400_BAD_REQUEST)

                # Save the booking
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Court.DoesNotExist:
                return Response({'error': 'Court not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
def venue_policy_view(request, venue_id):
    policy = CancellationAndRefund.objects.filter(venue_id=venue_id).first()

    if policy:
        cancellation_policy = policy.cancellationpolicy
        refund_policy = policy.refundpolicy
    else:
        cancellation_policy = "No cancellation policy available."
        refund_policy = "No refund policy available."

    results = {
        'cancellation_policy': cancellation_policy,
        'refund_policy': refund_policy
    }
    
    

    return render(request, 'venue_policy.html', {'results': results})



def register_venue_add(request, user_id):
    """Venue addition view with user ID pre-filled."""
    sports = Sporttype.objects.all()
    
    try:
        venue_owner = User.objects.get(id=user_id)  # Get venue owner by ID
        venue_owner_profile = venue_owner.venue_owner_profile
    except User.DoesNotExist:
        messages.error(request, "Venue owner not found.")
        return redirect('SportMeetApp:register-venue')  # Redirect to avoid errors

    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = venue_owner_profile  # Assign owner dynamically
            venue.save()

            # Save venue images
            images = request.FILES.getlist('images')
            VenueImage.objects.bulk_create([VenueImage(venue=venue, image=image) for image in images])

            # Save court requests
            try:
                sport = Sporttype.objects.get(id=request.POST['sport'])
                CourtRequest.objects.create(
                    venue=venue,
                    sport=sport,
                    court_count=int(request.POST['court_count']),
                    price=float(request.POST['price']),
                    duration=int(request.POST['duration'])
                )
            except Sporttype.DoesNotExist:
                messages.error(request, "Invalid sport type selected.")
                return redirect('register_venue_add', user_id=user_id)

            # **Do not regenerate token if already created in serializer**
            if not venue_owner.is_active:  # Only send verification if user is not yet verified
                token = EmailVerificationToken.objects.filter(user=venue_owner).first()
                if token:  # If token exists, reuse it
                    send_verification_email(request,venue_owner, token.token)

            messages.success(request, 'Venue added successfully!')
            return redirect('SportMeetApp:approval')  # Redirect to venue list page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VenueForm()

    return render(request, 'venue_add_register.html', {
        'form': form,
        'sports': sports,
        'user_id': user_id,
        'venue_owner_profile': venue_owner_profile,
       
    })





def dashboard(request):
    # Generate a list of months for the dropdown
    user = request.user
    months = []
    current_date = datetime.now()
    for i in range(12):  # Last 12 months
        month = current_date.strftime('%Y-%m')
        months.append(month)
        current_date = current_date.replace(day=1) - timedelta(days=1)  # Move to previous month
    
    if user.is_superuser :  # Admin or staff can see all venues
        venues = Venue.objects.filter(owner__is_approved=True)
    else:  # Venue owner can only see their own venues
        venue_owner = VenueOwnerProfile.objects.get(user=user)
        venues = Venue.objects.filter(owner=venue_owner) 
    
    current_month = datetime.now().strftime('%Y-%m')  # Current month in YYYY-MM format
    return render(request, 'dashboard.html', {'venues': venues, 'months': months, 'current_month': current_month})

def get_total_revenue(request):
    user = request.user

    if user.is_superuser:  # Admin can see revenue for all venues
        total_revenue = Booking.objects.aggregate(total_revenue=Sum('price'))['total_revenue'] or 0
    else:
        venue_owner = VenueOwnerProfile.objects.filter(user=user).first()
        if venue_owner:
            total_revenue = Booking.objects.filter(venue__owner=venue_owner).aggregate(total_revenue=Sum('price'))['total_revenue'] or 0
        else:
            total_revenue = 0  # If user is not a venue owner, revenue is 0

    return JsonResponse({'total_revenue': total_revenue})

def get_total_users(request):
    total_users = CustomerProfile.objects.count()
    return JsonResponse({'total_users': total_users})

def get_total_venues(request):
    user = request.user
    
    if user.is_superuser:  # Admin can see all approved venues
        total_venues = Venue.objects.filter(owner__is_approved=True).count()
    else:
        venue_owner = VenueOwnerProfile.objects.filter(user=user).first()
        if venue_owner:
            total_venues = Venue.objects.filter(owner=venue_owner).count()
        else:
            total_venues = 0  # If the user is not a venue owner, return 0

    return JsonResponse({'total_venues': total_venues})

def get_daywise_bookings(request, venue_id, month):
    # Fetch day-wise bookings for the selected venue and month
    bookings = Booking.objects.filter(venue_id=venue_id, date__startswith=month).values('date').annotate(total_bookings=Count('id'))
    
    # Prepare data for the chart
    data = {}
    for booking in bookings:
        # booking['date'] is already a datetime.date object
        day = booking['date'].strftime('%Y-%m-%d')  # Format as string
        data[day] = booking['total_bookings']
    
    return JsonResponse(data)

def get_weekwise_revenue(request, venue_id, month):
    # Fetch week-wise revenue for the selected venue and month
    bookings = Booking.objects.filter(venue_id=venue_id, date__startswith=month).values('date').annotate(total_revenue=Sum('price'))
    
    # Prepare data for the chart
    weekly_data = {}
    for booking in bookings:
        # booking['date'] is already a datetime.date object
        week = booking['date'].isocalendar()[1]  # Get ISO week number
        if week not in weekly_data:
            weekly_data[week] = 0
        weekly_data[week] += booking['total_revenue']
    
    return JsonResponse(weekly_data)



def venue_location(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)
    return render(request, "venue_location.html", {"venue": venue})

@csrf_exempt
def save_venue_location(request, venue_id):
    if request.method == "POST":
        venue = get_object_or_404(Venue, id=venue_id)
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if latitude and longitude:
            venue.latitude = latitude
            venue.longitude = longitude
            venue.save()
            return JsonResponse({
                "status": "success",
                "latitude": latitude,
                "longitude": longitude,
                "message": "Location saved successfully"
            })
        return JsonResponse({
            "status": "error",
            "message": "Invalid coordinates"
        }, status=400)
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)
    

from math import radians, sin, cos, sqrt, atan2
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * atan2(sqrt(a), sqrt(1-a))

def nearby_venues(request):
    try:
        user_lat = float(request.GET.get('lat'))
        user_lng = float(request.GET.get('lng'))
        radius_km = 5  # 5km radius
        
        # Get all venues with coordinates
        venues = Venue.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        
        # Calculate distance for each venue and filter
        nearby_venues = []
        for venue in venues:
            distance = haversine_distance(
                user_lat, user_lng,
                venue.latitude, venue.longitude
            )
            if distance <= radius_km:
                venue.distance = round(distance, 2)
                nearby_venues.append(venue)
        
        # Sort by distance
        nearby_venues.sort(key=lambda v: v.distance)
        
        return render(request, 'nearby_venues.html', {
            'venues': nearby_venues,
            'user_location': {'lat': user_lat, 'lng': user_lng}
        })
    
    except (TypeError, ValueError):
        return render(request, 'nearby_venues.html', {
            'error': 'Invalid coordinates provided'
        })
        
def reports_dashboard(request):
    # Get current month in YYYY-MM format
    current_month = timezone.now().strftime('%Y-%m')
    selected_month = request.GET.get('month', current_month)
    venue_id = request.GET.get('venue_id')
    
    # Generate months for dropdown (last 12 months)
    months = []
    date = timezone.now()
    for _ in range(12):
        months.append(date.strftime('%Y-%m'))
        # Move to previous month
        date = (date.replace(day=1) - timedelta(days=1))
    
    # Get venues for filter dropdown (admin only)
    venues = []
    if request.user.is_superuser:
        venues = Venue.objects.filter(owner__is_approved=True)
    
    # Base query for all reports
    if request.user.is_superuser:
        base_qs = Booking.objects.filter(date__year=selected_month[:4], 
                                       date__month=selected_month[5:7])
        if venue_id:
            base_qs = base_qs.filter(venue_id=venue_id)
    else:
        try:
            venue_owner = VenueOwnerProfile.objects.get(user=request.user)
            base_qs = Booking.objects.filter(
                venue__owner=venue_owner,
                date__year=selected_month[:4],
                date__month=selected_month[5:7]
            )
            if venue_id:
                base_qs = base_qs.filter(venue_id=venue_id)
        except VenueOwnerProfile.DoesNotExist:
            base_qs = Booking.objects.none()
    
    # Revenue Report Data - Top 10 venues
    revenue_data = list(base_qs.values(
        'venue__id', 'venue__name'
    ).annotate(
        total_revenue=Sum('price'),
        booking_count=Count('id')
    ).order_by('-total_revenue')[:10])
    
    # Daily Popular Timeslots
    daily_timeslots = list(base_qs.values(
        'date', 'start_time', 'end_time', 'venue__name'
    ).annotate(
        booking_count=Count('id')
    ).order_by('date', '-booking_count'))
    
    # Daily Popular Sports
    daily_sports = list(base_qs.values(
        'date', 'sport__name', 'venue__name'
    ).annotate(
        booking_count=Count('id')
    ).order_by('date', '-booking_count'))
    
    # Process daily data to get top entries per day
    processed_timeslots = {}
    for entry in daily_timeslots:
        date_str = entry['date'].strftime('%Y-%m-%d')
        if date_str not in processed_timeslots:
            processed_timeslots[date_str] = {
                'date': entry['date'],
                'timeslot': f"{entry['start_time']} - {entry['end_time']}",
                'venue': entry['venue__name'],
                'count': entry['booking_count']
            }
    
    processed_sports = {}
    for entry in daily_sports:
        date_str = entry['date'].strftime('%Y-%m-%d')
        if date_str not in processed_sports:
            processed_sports[date_str] = {
                'date': entry['date'],
                'sport': entry['sport__name'],
                'venue': entry['venue__name'],
                'count': entry['booking_count']
            }
    
    context = {
        'months': months,
        'venues': venues,
        'current_month': current_month,
        'selected_month': selected_month,
        'selected_venue': int(venue_id) if venue_id else None,
        'revenue_data': revenue_data,
        'daily_timeslots': list(processed_timeslots.values()),
        'daily_sports': list(processed_sports.values()),
    }
    
    return render(request, 'dashboard_reports.html', context)

# class BookingCreateAPIView(APIView):
#     def post(self, request, *args, **kwargs):
#         mutable_data = request.data.copy()
#         is_venue_owner = hasattr(request.user, 'venue_owner_profile')

#         # Handle customer assignment
#         if is_venue_owner:
#             if 'customer_name' in mutable_data and mutable_data['customer_name']:
#                 customer_name = mutable_data['customer_name']
#                 temp_username = customer_name.lower().replace(" ", "_")
#                 user, created = User.objects.get_or_create(
#                     username=temp_username,
#                     defaults={
#                         "first_name": customer_name.split()[0],
#                         "last_name": " ".join(customer_name.split()[1:]) if " " in customer_name else "",
#                     }
#                 )
#                 customer_profile, _ = CustomerProfile.objects.get_or_create(user=user)
#                 mutable_data['customer'] = customer_profile.id
#                 mutable_data['venue_owner'] = request.user.venue_owner_profile.id
#             else:
#                 return Response({'error': 'Customer information is required.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             if request.user.is_authenticated:
#                 customer_profile = CustomerProfile.objects.get_or_create(user=request.user)[0]
#                 mutable_data['customer'] = customer_profile.id
#             else:
#                 return Response({'error': 'Authentication required for customers.'}, status=status.HTTP_401_UNAUTHORIZED)

#         # Validate booking data
#         serializer = BookingSerializer(data=mutable_data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Check for overlapping bookings
#         try:
#             court = Court.objects.get(id=mutable_data['court'])
#             if Booking.objects.filter(
#                 court=court,
#                 date=mutable_data['date'],
#                 start_time__lt=mutable_data['end_time'],
#                 end_time__gt=mutable_data['start_time'],
#                 booking_status__in=['pending', 'confirmed'],
#             ).exists():
#                 return Response({'error': 'This court is already booked.'}, status=status.HTTP_400_BAD_REQUEST)
#         except Court.DoesNotExist:
#             return Response({'error': 'Court not found'}, status=status.HTTP_400_BAD_REQUEST)

#         # Save booking with pending status
#         booking = serializer.save(booking_status='pending')
#         booking_data = serializer.data

#         # Create transaction record
#         transaction = Transaction.objects.create(
#             booking=booking,
#             amount=booking.price,
#             currency='AUD',
#             payment_method='payrexx' if not is_venue_owner else 'offline',
#             payment_status='pending'
#         )

#         # For venue owners, confirm immediately
#         if is_venue_owner:
#             transaction.mark_as_paid(payment_method='offline')
#             return Response(booking_data, status=status.HTTP_201_CREATED)

#         # For customers, process payment
#         params = {
#             "amount": str(int(booking.price * 100)),
#             "currency": "AUD",
#             "purpose": f"Booking #{booking.booking_id}",
#             "successRedirectUrl": request.build_absolute_uri(
#                 reverse('booking_payment_success', kwargs={'transaction_id': str(transaction.transaction_id)})
#             ),
#             "failedRedirectUrl": request.build_absolute_uri(
#                 reverse('booking_payment_failed', kwargs={'transaction_id': str(transaction.transaction_id)})
#             ),
#             "cancelRedirectUrl": request.build_absolute_uri(
#                 reverse('booking_payment_canceled', kwargs={'transaction_id': str(transaction.transaction_id)})
#             ),
#             "referenceId": str(transaction.transaction_id),
#             "fields": {
#                 "forename": customer_profile.user.first_name,
#                 "surname": customer_profile.user.last_name,
#                 "email": customer_profile.user.email,
#             }
#         }

#         response = requests.post(
#             f"{settings.PAYREXX_CONFIG['ENDPOINT']}Invoice.json",
#             auth=(settings.PAYREXX_CONFIG['INSTANCE_NAME'], settings.PAYREXX_CONFIG['API_KEY']),
#             headers={'Content-Type': 'application/json'},
#             data=json.dumps(params)
#         )

#         if response.status_code == 200:
#             data = response.json()
#             transaction.gateway_reference = data['data']['id']
#             transaction.save()
#             return Response({
#                 'status': 'payment_required',
#                 'payment_url': data['data']['link']['href'],
#                 'booking_data': booking_data
#             }, status=status.HTTP_200_OK)
#         else:
#             booking.delete()
#             return Response({'error': 'Payment gateway error'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# class BookingPaymentSuccessView(APIView):
#     def get(self, request, transaction_id, *args, **kwargs):
#         try:
#             transaction = Transaction.objects.get(transaction_id=transaction_id)
#             transaction.mark_as_paid(
#                 gateway_reference=request.GET.get('transaction_id'),
#                 payment_method='payrexx',
#                 response_data=dict(request.GET)
#             )
#             return Response({'status': 'Booking confirmed'})
#         except Transaction.DoesNotExist:
#             return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

# class BookingPaymentFailedView(APIView):
#     def get(self, request, transaction_id, *args, **kwargs):
#         try:
#             transaction = Transaction.objects.get(transaction_id=transaction_id)
#             transaction.payment_status = 'failed'
#             transaction.save()
#             return Response({'status': 'Payment failed'})
#         except Transaction.DoesNotExist:
#             return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

# class BookingPaymentCanceledView(APIView):
#     def get(self, request, transaction_id, *args, **kwargs):
#         try:
#             transaction = Transaction.objects.get(transaction_id=transaction_id)
#             transaction.payment_status = 'canceled'
#             transaction.save()
#             return Response({'status': 'Payment canceled'})
#         except Transaction.DoesNotExist:
#             return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

# @csrf_exempt
# def payrexx_webhook(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             transaction_id = data.get('referenceId')
#             status = data.get('status')
            
#             if transaction_id and status:
#                 try:
#                     transaction = Transaction.objects.get(transaction_id=transaction_id)
#                     if status.lower() == 'confirmed':
#                         transaction.mark_as_paid(
#                             gateway_reference=data.get('id'),
#                             payment_method='payrexx',
#                             response_data=data
#                         )
#                     elif status.lower() == 'failed':
#                         transaction.payment_status = 'failed'
#                         transaction.save()
#                     elif status.lower() == 'canceled':
#                         transaction.payment_status = 'canceled'
#                         transaction.save()
#                 except Transaction.DoesNotExist:
#                     pass
#         except json.JSONDecodeError:
#             pass
#     return HttpResponse(status=200)
        
        