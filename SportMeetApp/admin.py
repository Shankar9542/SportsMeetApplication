from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from .models import *
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, path, reverse
from django.utils.html import format_html
from django.contrib.auth.forms import UserChangeForm
from django.utils.timezone import now
from django.contrib import messages
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.db.models import Avg, OuterRef, Subquery,Count
from .models import Rating
from .utils.email_utils import send_verification_email
from.views import *
from django.contrib.admin import AdminSite
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator

class VenueImageInline(admin.StackedInline):
    model = VenueImage
    extra = 1



class CourtInline(admin.StackedInline):  
    """ Inline to display courts in the Venue admin panel (edit mode) """
    model = Court
    extra = 0  # Users can add multiple courts inline


class CourtRequestInline(admin.StackedInline):
    model = CourtRequest
    extra = 1

    def save_model(self, request, obj, form, change):
        """
        Override save to create courts dynamically and remove the CourtRequest entry.
        """
        obj.save()
        existing_courts = Court.objects.filter(venue=obj.venue, sport=obj.sport).count()
        for i in range(1, obj.court_count + 1):
            Court.objects.create(
                venue=obj.venue,
                sport=obj.sport,
                court_number=existing_courts + i,  # Assign unique court numbers
                price=obj.price,
            )
        obj.delete()  # Remove CourtRequest after processing

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(venue__owner=request.user.venue_owner_profile)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            try:
                venue_owner = VenueOwnerProfile.objects.get(user=request.user)
                kwargs["initial"] = venue_owner.id
                kwargs["queryset"] = VenueOwnerProfile.objects.filter(user=request.user)
            except VenueOwnerProfile.DoesNotExist:
                kwargs["queryset"] = VenueOwnerProfile.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        Override save to create courts dynamically and remove the CourtRequest entry.
        """
        obj.save()
        existing_courts = Court.objects.filter(venue=obj.venue, sport=obj.sport).count()
        for i in range(1, obj.court_count + 1):
            Court.objects.create(
                venue=obj.venue,
                sport=obj.sport,
                court_number=existing_courts + i,  # Assign unique court numbers
                price=obj.price,
            )
        obj.delete()  # Remove CourtRequest after processing




    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(venue__owner=request.user.venue_owner_profile)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            try:
                venue_owner = VenueOwnerProfile.objects.get(user=request.user)
                kwargs["initial"] = venue_owner.id
                kwargs["queryset"] = VenueOwnerProfile.objects.filter(user=request.user)
            except VenueOwnerProfile.DoesNotExist:
                kwargs["queryset"] = VenueOwnerProfile.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class SportAdmin(admin.ModelAdmin):
    model = Sporttype
    list_display = ['name','image','actions_column']
    
    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        try:
            # Generate the URL for the change page
            change_url = reverse("admin:SportMeetApp_sporttype_change", args=[obj.id])
            # Material icon for "visibility"
            eye_icon = '<span class="material-symbols-outlined"style="color: blue;">visibility</span>'
            # Wrap the icon in a link to the change page
            return format_html('<a href="{}" class="action-icon">{}</a>', change_url, format_html(eye_icon))
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"
 
    actions_column.short_description =  mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    ) 
    
class CancellationAndRefundInline(admin.StackedInline):
    model = CancellationAndRefund
    extra = 0  # Allows users to input number o


from django.contrib.admin.filters import SimpleListFilter

class VenueOwnerVenueFilter(SimpleListFilter):
    """Custom filter to show only the venues owned by the venue owner"""
    title = 'Venue'
    parameter_name = 'venue'

    def lookups(self, request, model_admin):
        """Limit venue choices for venue owners"""
        if request.user.is_superuser:
            return Venue.objects.values_list('id', 'name')  # Admins see all venues

        elif hasattr(request.user, 'venue_owner_profile'):
            owner_venues = Venue.objects.filter(owner=request.user.venue_owner_profile)
            return [(v.id, v.name) for v in owner_venues]  # Venue owner sees only their venues

        return []

    def queryset(self, request, queryset):
        """Filter queryset based on selected venue"""
        if self.value():
            return queryset.filter(venue_id=self.value())
        return queryset
    
class BookingAdmin(admin.ModelAdmin):
    model = Booking
    list_display = ['booking_id', 'venue', 'court_number', 'date', 'price', 'start_time', 'end_time', 'mode_of_payment', "actions_column"]
    search_fields = ('venue__name', 'customer__user__username',  'court__court_number') 
    # list_filter = ('booking_status', 'venue', 'date')
    list_per_page = 5
    _current_request = None  # Store request object

    def get_queryset(self, request):
        """Filter queryset based on user role"""
        self._current_request = request  # Store request
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs  # Admin sees all bookings
        elif hasattr(request.user, 'venue_owner_profile'):
            return qs.filter(venue__owner=request.user.venue_owner_profile)  # Venue Owner sees their venue bookings only
        elif hasattr(request.user, 'customer_profile'):
            return qs.filter(customer=request.user.customer_profile)  # Customer sees only their bookings
        return qs.none()
    
    

    def get_list_filter(self, request):
        """Set filters dynamically based on user role"""
        if request.user.is_superuser:
            return ('venue', 'booking_status', 'date')  # Admins see all venues

        elif hasattr(request.user, 'venue_owner_profile'):
            return ('booking_status', 'date', VenueOwnerVenueFilter)  # Venue owners see only their venues

        elif hasattr(request.user, 'customer_profile'):
            return ('date',)  # Customers filter by status & date only

        return ()

    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit venue choices in forms for venue owners"""
        if db_field.name == "venue" and hasattr(request.user, 'venue_owner_profile'):
            kwargs["queryset"] = Venue.objects.filter(owner=request.user.venue_owner_profile)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def venue(self, obj):
        return obj.venue.name  
    venue.admin_order_field = 'venue__name'
    venue.short_description = 'Venue Name'

    def court_number(self, obj):
        return obj.court.court_number  
    court_number.admin_order_field = 'court__court_number'
    court_number.short_description = 'Court No'

    def actions_column(self, obj):
        """Generate view and delete action links based on user permissions"""
        if not obj.id:
            return "No ID"

        try:
            change_url = reverse("admin:SportMeetApp_booking_change", args=[obj.id])
            eye_icon = '<span class="material-symbols-outlined" style="color: blue;">visibility</span>'
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))

            request = self._current_request  # Get stored request
            delete_link = ""
            if request and request.user.has_perm("SportMeetApp.delete_booking"):
                delete_url = reverse("admin:SportMeetApp_booking_delete", args=[obj.id])
                delete_icon = '<span class="material-symbols-outlined" style="color: red;">delete</span>'
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))

            return format_html('{} {}', view_link, delete_link)

        except NoReverseMatch:
            return "Invalid URL"

    actions_column.short_description = mark_safe('<a href="#" onclick="return false;">Actions</a>')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('venue-owner-booking-view/', venue_owner_booking_view, name='venue-owner-booking-view'),
        ]
        return custom_urls + urls
 
class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', dashboard, name='dashboard'),
            path('dashboard-reports/', reports_dashboard, name='dashboard-reports'),
        ]
        return custom_urls + urls

# Replace the default admin site with your custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')
    
class CourtAdmin(admin.ModelAdmin):
    model = Court
    list_display = ['venue', 'sport', 'court_number', 'price', 'duration']
  
  
    


class RatingAdmin(admin.ModelAdmin):
    model = Rating
    # list_display = ("venue", ")
    # list_display_links = ("venue",)
    search_fields = ('venue__name', 'customer__user__username')
    list_filter = ('venue__name', 'rating', 'created_at')
    # Make some fields read-only
    readonly_fields = ['customer', 'venue', 'rating', 'review', 'created_at', 'replied_at']

    def get_queryset(self, request):
        # Use a subquery to calculate the average rating for each venue
        avg_rating_subquery = (
            Rating.objects.filter(venue=OuterRef('venue'))
            .values('venue')
            .annotate(avg_rating=Avg('rating'))
            .values('avg_rating')
        )

        # Annotate the main queryset with the average rating
        qs = super().get_queryset(request).annotate(
            overall_average_rating=Subquery(avg_rating_subquery)
        )


    
        if request.user.is_superuser:
            return qs  # Superusers see all ratings
        
        if hasattr(request.user, 'venue_owner_profile'):
            # Show ratings for venues owned by the logged-in venue owner
            return qs.filter(venue__owner=request.user.venue_owner_profile)
        
        if hasattr(request.user, 'customer_profile'):
            # Show ratings created by the logged-in customer
            return qs.filter(customer=request.user.customer_profile)
        
        return qs.none()  # If the user has no relevant profile, return empty queryset

    def has_change_permission(self, request, obj=None):
        """Restrict editing except for replying to ratings."""
        if obj and hasattr(request.user, 'venue_owner_profile'):
            # Allow venue owner to reply to their own venue's ratings only
            return obj.venue.owner == request.user.venue_owner_profile
        return request.user.is_superuser  # Only superusers can edit everything

    def has_delete_permission(self, request, obj=None):
        """Disable delete option for venue owners."""
        return request.user.is_superuser  # Only superusers can delete ratings

    def save_model(self, request, obj, form, change):
        """Ensure only venue owners can reply to ratings for their own venues."""
        if obj.pk:  # Ensure it's an existing rating
            if hasattr(request.user, 'venue_owner_profile') and obj.venue.owner == request.user.venue_owner_profile:
                obj.replied_at = now()  # Update reply timestamp
                super().save_model(request, obj, form, change)
            else:
                messages.error(request, "You can only reply to reviews for your own venues.")
        else:
            super().save_model(request, obj, form, change)
    def venue_name(self, obj):
        """Display the venue name directly"""
        return obj.venue.name

    def overall_average_rating(self, obj):
        """Round the overall average rating for display"""
        return round(obj.overall_average_rating, 2) if obj.overall_average_rating else "N/A"

    venue_name.admin_order_field = 'venue__name'
    venue_name.short_description = "Venue"

    overall_average_rating.admin_order_field = 'overall_average_rating'
    overall_average_rating.short_description = "Overall Average Rating"
    
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to the custom venue list view
        return self.venue_list_view(request)
 
    def get_urls(self):
        # Add custom URLs for the admin
        urls = super().get_urls()
        custom_urls = [
            path("venue-list/", self.admin_site.admin_view(self.venue_list_view), name="venue_list"),
            path("venue/<int:venue_id>/reviews/", self.admin_site.admin_view(self.venue_reviews), name="venue_reviews"),
            path("<int:rating_id>/delete/", self.admin_site.admin_view(self.delete_rating), name="core_rating_delete"),
        ]
        return custom_urls + urls


    def venue_list_view(self, request):
        # Get all filter parameters
        params = request.GET.copy()
        # Base queryset with permissions
        if request.user.is_superuser:
            venues = Venue.objects.all()
        elif hasattr(request.user, 'venue_owner_profile'):
            venues = Venue.objects.filter(owner=request.user.venue_owner_profile)
        else:
            venues = Venue.objects.none()
    
        # Search functionality (independent)
        if 'q' in params:
            venues = venues.filter(name__icontains=params['q'])
    
        # Rating filter (independent)
        if 'rating' in params:
            try:
                rating_value = float(params['rating'])
                venues = venues.annotate(
                    avg_rating=Avg('ratings__rating')
                ).filter(avg_rating__gte=rating_value)
            except (ValueError, TypeError):
                pass  # Ignore invalid rating values
    
        # Date filter (independent)
        if 'date_range' in params:
            today = timezone.now().date()
            if params['date_range'] == 'today':
                start_date = today
            elif params['date_range'] == 'week':
                start_date = today - timedelta(days=7)
            elif params['date_range'] == 'month':
                start_date = today.replace(day=1)
            elif params['date_range'] == 'year':
                start_date = today.replace(month=1, day=1)
            if start_date:
                venues = venues.filter(
                    ratings__created_at__date__gte=start_date
                ).distinct()
    
        # Sorting
        sort_options = {
            'newest': '-ratings__created_at',
            'oldest': 'ratings__created_at',
            'highest': '-avg_rating',
            'lowest': 'avg_rating',
            'default': '-avg_rating'
        }
        # Get sort parameter or use default
        sort_param = params.get('sort', 'default')
        sort_by = sort_options.get(sort_param, '-avg_rating')
        # Final annotations and ordering
        venues = venues.annotate(
            avg_rating=Avg('ratings__rating'),
            total_reviews=Count('ratings'),
        ).order_by(sort_by)
    
        # Pagination
        paginator = Paginator(venues, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "venues": page_obj,
            "current_params": params,
        }
        return render(request, "admin/venue_list.html", context)


    
    def delete_rating(self, request, rating_id):
        # Handle rating deletion
        rating = Rating.objects.get(id=rating_id)
        rating.delete()
        return redirect("admin:core_rating_changelist")
 
    def venue_reviews(self, request, venue_id):
        venue = Venue.objects.get(id=venue_id)
        reviews = Rating.objects.filter(venue=venue)
        # Get all filter parameters
        params = request.GET.copy()
        # Search functionality
        if 'q' in params and params['q']:
            reviews = reviews.filter(
                Q(customer__user__username__icontains=params['q']) |
                Q(review__icontains=params['q']) |
                Q(owner_reply__icontains=params['q'])
            )
        # Rating filter
        if 'rating' in params and params['rating']:
            reviews = reviews.filter(rating=params['rating'])
        # Date filter
        if 'date' in params and params['date']:
            today = timezone.now().date()
            if params['date'] == 'today':
                reviews = reviews.filter(created_at__date=today)
            elif params['date'] == 'week':
                reviews = reviews.filter(created_at__date__gte=today - timedelta(days=7))
            elif params['date'] == 'month':
                reviews = reviews.filter(created_at__date__gte=today.replace(day=1))
        # Sorting
        sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'highest': '-rating',
            'lowest': 'rating'
        }
        sort_by = sort_options.get(params.get('sort', 'newest'), '-created_at')
        reviews = reviews.order_by(sort_by)
        context = {
            **self.admin_site.each_context(request),
            "venue": venue,
            "reviews": reviews,
            "current_params": params,
        }
        return render(request, "admin/venue_reviews.html", context)
    
    # def actions_column(self, obj):
    #     # Debugging: Check if obj.id is valid
    #     if not obj.id:
    #         return "No ID"
    #     try:
    #         # Generate the URL for the change page
    #         change_url = reverse("admin:SportMeetApp_rating_change", args=[obj.id])
    #         # Material icon for "visibility"
    #         eye_icon = '<span class="material-symbols-outlined">visibility</span>'
    #         # Wrap the icon in a link to the change page
    #         return format_html('<a href="{}" class="action-icon">{}</a>', change_url, format_html(eye_icon))
    #     except NoReverseMatch:
    #         # Handle the case where the URL pattern is not found
    #         return "Invalid URL"
 
    # actions_column.short_description =  mark_safe(
    #     '<a href="#" onclick="return false;">Actions</a>'
    # ) 


class VenueAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "area", "get_court_count", "get_sports_list",'start_time', 'end_time','actions_column']
    inlines = [VenueImageInline, CourtRequestInline,CourtInline, CancellationAndRefundInline]
    search_fields =['name']
    list_filter=['name']
    # fields = ["name", "area", "latitude", "longitude", "location_button"]  # Show in details view
    
    
    readonly_fields = ['location_button']  # Crucial for the button to appear
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/save-location/', self.save_location, name='save_venue_location'),
        ]
        return custom_urls + urls
    
    def save_location(self, request, object_id):
        venue = get_object_or_404(Venue, id=object_id)
        if request.method == "POST":
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            
            if latitude and longitude:
                venue.latitude = latitude
                venue.longitude = longitude
                venue.save()
                return JsonResponse({"status": "success"})
            return JsonResponse({"status": "error"}, status=400)
        return JsonResponse({"status": "error"}, status=405)
    
    def location_button(self, obj):
        if not obj.pk:
            return "Save the venue first"
            
        url = reverse('SportMeetApp:save_venue_location', args=[obj.pk])
        return format_html(
            '''
            <button onclick="getAndSaveLocation(event, '{}')"
                    style="background:#007bff;color:white;padding:8px 12px;border:none;border-radius:5px;cursor:pointer;">
                📍 Locate Venue
            </button>
            <script>
                function getAndSaveLocation(event, url) {{
                    event.preventDefault();
                    if (navigator.geolocation) {{
                        navigator.geolocation.getCurrentPosition(
                            async (position) => {{
                                const formData = new FormData();
                                formData.append('latitude', position.coords.latitude);
                                formData.append('longitude', position.coords.longitude);
                                formData.append('csrfmiddlewaretoken', '{}');
                                
                                try {{
                                    const response = await fetch(url, {{
                                        method: 'POST',
                                        body: formData
                                    }});
                                    const result = await response.json();
                                    
                                    if (result.status === 'success') {{
                                        // Update the latitude/longitude fields without refresh
                                        document.getElementById('id_latitude').value = position.coords.latitude;
                                        document.getElementById('id_longitude').value = position.coords.longitude;
                                        alert('Location saved successfully!');
                                    }} else {{
                                        alert('Error saving location');
                                    }}
                                }} catch (error) {{
                                    alert('Network error: ' + error.message);
                                }}
                            }},
                            (error) => {{
                                alert('Geolocation error: ' + error.message);
                            }}
                        );
                    }} else {{
                        alert('Geolocation not supported by your browser');
                    }}
                }}
            </script>
            ''',
            url,
            '{{ csrf_token }}'
        )
    location_button.short_description = "Auto Location"


    
    def get_court_count(self, obj):
        """Returns the number of courts available in a venue."""
        return obj.courts.count()

    get_court_count.short_description = "Courts"
    get_court_count.admin_order_field = "courts__count"  # Enable sorting

    def get_sports_list(self, obj):
        """Returns a comma-separated list of unique sport names available in the venue."""
        sports = Sporttype.objects.filter(courts__venue=obj).distinct()
        return ", ".join([sport.name for sport in sports]) if sports else "No Sports"

        

    get_sports_list.short_description =  mark_safe(
        '<a href="#" onclick="return false;">Sports</a>'
    ) 

    def get_queryset(self, request):
        self.request = request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superuser should see all venues
        return qs.filter(owner=getattr(request.user, 'venue_owner_profile', None))  # Prevents AttributeError if no profile exists

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            kwargs["label"] = "ID"
            if request.user.is_superuser:
                kwargs["queryset"] = VenueOwnerProfile.objects.all()  # Allow superuser to see all owners
            else:
                try:
                    venue_owner = VenueOwnerProfile.objects.get(user=request.user)
                    kwargs["initial"] = venue_owner.id
                    kwargs["queryset"] = VenueOwnerProfile.objects.filter(user=request.user)
                except VenueOwnerProfile.DoesNotExist:
                    kwargs["queryset"] = VenueOwnerProfile.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_inline_instances(self, request, obj=None):
        inlines = []
        
        if obj is None:  # When adding a new venue
            inlines.append(CourtRequestInline(self.model, self.admin_site))
        else:  # When editing an existing venue
            inlines.append(CourtInline(self.model, self.admin_site))

        # Always include VenueImageInline
        inlines.append(VenueImageInline(self.model, self.admin_site))
        inlines.append(CancellationAndRefundInline(self.model, self.admin_site))

        return inlines
    
    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change page (view action)
            change_url = reverse("admin:SportMeetApp_venue_change", args=[obj.id])
            # Generate the URL for the delete page (delete action)
            delete_url = reverse("admin:SportMeetApp_venue_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined"style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined" style="color: red;">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = ''
            if self.has_delete_permission(self.request, obj):
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    ) 
    
    # def has_add_permission(self, request):
    #     """Only allow users with the 'add_venue' permission to add venues."""
    #     return request.user.has_perm('SportMeetApp.add_venue')
    
    # def get_form(self, request, obj=None, **kwargs):
    #     """Pre-fill the owner field with the logged-in user's VenueOwnerProfile."""
    #     form = super().get_form(request, obj, **kwargs)
    #     if not obj:  # Only when adding a new venue
    #         try:
    #             venue_owner_profile = request.user.venue_owner_profile
    #             form.base_fields['owner'].initial = venue_owner_profile
    #         except AttributeError:
    #             pass  # Handle the case where the user doesn't have a VenueOwnerProfile
    #     return form
    # def save_model(self, request, obj, form, change):
    #     """
    #     Override the save_model method to trigger email verification after saving the venue.
    #     """
    #     # Save the venue first
    #     super().save_model(request, obj, form, change)

    #     # If the venue is being added (not changed), trigger email verification
    #     if not change:
    #         user = obj.owner.user  # Get the user associated with the venue owner
    #         token = EmailVerificationToken.objects.create(user=user)
    #         send_verification_email(user, token.token)
    #         messages.success(request, "Venue details saved successfully! Please check your email to verify your account.")

    # def response_add(self, request, obj, post_url_continue=None):
    #     """
    #     Override the response after adding a venue to redirect to the home page.
    #     """
    #     return HttpResponseRedirect(reverse('approval_page'))  # Redirect to home page


    
# Registering models
class VenueOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'user__email', 'is_approved', 'created_at', 'actions_column')
    list_filter = ['is_approved']
    search_fields = ('user__username', 'user__email', 'phone')  
    actions = ['approve_venue_owners']
    
    def get_queryset(self, request):
        # Store the request for later use in actions_column
        self.request = request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Show all for superusers
        return qs.filter(user=request.user)  # Only show the logged-in venue owner
        
    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change page (view action)
            change_url = reverse("admin:SportMeetApp_venueownerprofile_change", args=[obj.id])
            # Generate the URL for the delete page (delete action)
            delete_url = reverse("admin:SportMeetApp_venueownerprofile_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined"style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined"style="color: red;">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = ''
            if self.has_delete_permission(self.request, obj):
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if not request.user.is_superuser:  # Only filter for non-admin users
                kwargs["queryset"] = User.objects.filter(id=request.user.id)  # Show only the logged-in user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)    
    
  

   



@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone', 'user_email', 'actions_column']
    search_fields = ['user__username', 'user__email', 'phone']
    
    
    def get_queryset(self, request):
        # Store the request for later use in actions_column
        self.request = request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
        
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def actions_column(self, obj):
        if not obj.id:
            return "No ID"
        
        try:
            change_url = reverse("admin:SportMeetApp_customerprofile_change", args=[obj.id])
            delete_url = reverse("admin:SportMeetApp_customerprofile_delete", args=[obj.id])
            
            eye_icon = '<span class="material-symbols-outlined"style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined"style="color: red;">delete</span>'
            
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            
            # Only show delete link if user has permission
            delete_link = ''
            if self.has_delete_permission(self.request, obj):
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if not request.user.is_superuser:
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


    
CustomUser = get_user_model()


# Custom Form (Excludes password field and permissions)
class CustomUserAdmin(UserAdmin):
    # Use the default UserChangeForm to ensure the password reset link is rendered
    form = UserChangeForm

    # Define the fieldsets to include the password field
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
    
    )

    # Optional: Add a custom reset password link in the list view
    list_display = ("id","username", "email","get_phone","get_role","actions_column")
    list_filter = ["groups"]

    def reset_password_link(self, obj):
        url = reverse("admin:auth_user_password_change", args=[obj.pk])
        return format_html(f'<a href="{url}" class="button">Reset Password</a>')

    reset_password_link.short_description = "Reset Password"
    
    def get_role(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_role.short_description = mark_safe(
        '<a href="#" onclick="return false;">Role</a>'
    )
    
    def get_phone(self, obj):
        """Fetch phone number from CustomerProfile or VenueOwnerProfile"""
        if hasattr(obj, "customer_profile") and obj.customer_profile.phone:
            return obj.customer_profile.phone
        elif hasattr(obj, "venue_owner_profile") and obj.venue_owner_profile.phone:
            return obj.venue_owner_profile.phone
        return "N/A"  # Default value if no phone is found
    get_phone.short_description = mark_safe(
        '<a href="#" onclick="return false;">mobile</a>'
    )
    
    def get_queryset(self, request):
        # Store the request for permission checks
        self.request = request
        return super().get_queryset(request)

    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change page (view action)
            change_url = reverse("admin:auth_user_change", args=[obj.id])
            # Generate the URL for the delete page (delete action)
            delete_url = reverse("admin:auth_user_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined"style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined"style="color: red;">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            # Delete link (only visible if user has delete permission)
            delete_link = ''
            if self.has_delete_permission(self.request, obj):
                delete_link = format_html(
                    '<a href="{}" class="action-icon" title="Delete">{}</a>', 
                    delete_url, 
                    format_html(delete_icon)
                )
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    ) 

class DiscountAdmin(admin.ModelAdmin):
    list_display = ("venue", "discount", "actions_column")

    def get_queryset(self, request):
        """Restrict venue owners to see only their venue discounts."""
        self._current_request = request  # Store the request object
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superuser sees all discounts
        return qs.filter(venue__owner=getattr(request.user, 'venue_owner_profile', None))

    def actions_column(self, obj):
        """Add view and delete actions as icons in the admin panel."""
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change (edit) and delete pages
            change_url = reverse("admin:SportMeetApp_discount_change", args=[obj.id])
            delete_url = reverse("admin:SportMeetApp_discount_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined" style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined" style="color: red;">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))

            # The delete link should only be visible if the user has delete permission
            request = getattr(self, '_current_request', None)  # Get stored request
            delete_link = ''
            if request and self.has_delete_permission(request, obj):
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))

            return format_html('{} {}', view_link, delete_link)
        
        except NoReverseMatch:
            return "Invalid URL"

    

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )
    
    
    
class CancellationAndRefundAdmin(admin.ModelAdmin):
    list_display = ('venue', 'actions_column')

    def get_queryset(self, request):
        """Restrict venue owners to see only their venue discounts."""
        self._current_request = request  # Store the request object
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superuser sees all discounts
        return qs.filter(venue__owner=getattr(request.user, 'venue_owner_profile', None))
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "venue":
            if request.user.is_superuser:
                kwargs["queryset"] = Venue.objects.all()  # Superuser sees all venues
            else:
                try:
                    venue_owner = VenueOwnerProfile.objects.get(user=request.user)
                    kwargs["queryset"] = Venue.objects.filter(owner=venue_owner)  # Venue owners only see their venues
                except VenueOwnerProfile.DoesNotExist:
                    kwargs["queryset"] = Venue.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def actions_column(self, obj):
        """Add view and delete actions as icons in the admin panel."""
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change (edit) and delete pages
            change_url = reverse("admin:SportMeetApp_cancellationandrefund_change", args=[obj.id])
            delete_url = reverse("admin:SportMeetApp_cancellationandrefund_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined" style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined" style="color: red;">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))

            # The delete link should only be visible if the user has delete permission
            request = getattr(self, '_current_request', None)  # Get stored request
            delete_link = ''
            if request and self.has_delete_permission(request, obj):
                delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))

            return format_html('{} {}', view_link, delete_link)
        
        except NoReverseMatch:
            return "Invalid URL"

 

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )


# Unregister the default User model
admin.site.unregister(User)

# Register the custom UserAdmin
admin.site.register(User, CustomUserAdmin)




    
admin.site.register(Venue, VenueAdmin)
admin.site.register(CancellationAndRefund,CancellationAndRefundAdmin)
admin.site.register(VenueImage)
admin.site.register(Court,CourtAdmin)
admin.site.register(Sporttype, SportAdmin)
admin.site.register(Banner)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(VenueOwnerProfile, VenueOwnerProfileAdmin)
# admin.site.register(Coupon)
admin.site.register(Discount,DiscountAdmin)