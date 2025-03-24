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
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.db.models import Avg, OuterRef, Subquery,Count
from .models import Rating
from .utils.email_utils import send_verification_email
from.views import *
from django.contrib.admin import AdminSite

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
            eye_icon = '<span class="material-symbols-outlined">visibility</span>'
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

class BookingAdmin(admin.ModelAdmin):
    model = Booking
    list_display =['booking_id', 'venue', 'court_number', 'date', 'price', 'start_time', 'end_time', 'mode_of_payment',"actions_column"]
    search_fields = ('venue__name', 'customer__user__username',  'court__court_number') 
    list_filter = ('booking_status', 'venue', 'date')
    list_per_page=5
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'venue_owner_profile'):
            # Filter bookings for venue owner
            return qs.filter(venue__owner=request.user.venue_owner_profile)
        elif hasattr(request.user, 'customer_profile'):
            # Filter bookings for customer
            return qs.filter(customer=request.user.customer_profile)
        return qs.none()
   
    def venue(self, obj):
        return obj.venue.name  # Display venue name
    venue.admin_order_field = 'venue__name'  # Allow sorting by venue name
    venue.short_description = 'Venue Name'  # Set column title in admin panel
   
    def court_number(self, obj):
        return obj.court.court_number  # Display court number
    court_number.admin_order_field = 'court__court_number'  # Allow sorting by court number
    court_number.short_description = 'Court No'  # Set column title in admin panel

    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change page (view action)
            change_url = reverse("admin:SportMeetApp_booking_change", args=[obj.id])
            # Generate the URL for the delete page (delete action)
            delete_url = reverse("admin:SportMeetApp_booking_delete", args=[obj.id])

            # Material icons with custom styling
            eye_icon = '<span class="material-symbols-outlined" style="color: blue;">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined" style="color: red;">delete</span>'  # Red color

            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))

            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)

        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )
    
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
        # Calculate average rating and total reviews for each venue
        venues = Venue.objects.annotate(
            average_rating=Avg("ratings__rating"),
            total_reviews=Count("ratings"),
        )
 
        # Create a change list object
        cl = self.get_changelist_instance(request)
        actions=self.get_actions(request)
 
        # Render the custom template
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "venues": venues,
            "cl": cl,  # Pass the change list object for actions dropdown
            "actions":actions
        }
        return render(request, "admin/venue_list.html", context)
    
    def delete_rating(self, request, rating_id):
        # Handle rating deletion
        rating = Rating.objects.get(id=rating_id)
        rating.delete()
        return redirect("admin:core_rating_changelist")
 
    def venue_reviews(self, request, venue_id):
        # Display all reviews for a specific venue
        venue = Venue.objects.get(id=venue_id)
        reviews = Rating.objects.filter(venue=venue)
 
        # Render the custom template
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "venue": venue,
            "reviews": reviews,
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
            eye_icon = '<span class="material-symbols-outlined">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
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
    list_display = ('id','user', 'phone','user__email', 'is_approved', 'created_at', 'actions_column')
    list_filter = ['is_approved']
    search_fields = ('user__username', 'user__email', 'phone')  
    actions = ['approve_venue_owners']
    
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
            eye_icon = '<span class="material-symbols-outlined">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    ) 
    
    
  

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Show all for superusers
        return qs.filter(user=request.user)  # Only show the logged-in venue owner

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if not request.user.is_superuser:  # Only filter for non-admin users
                kwargs["queryset"] = User.objects.filter(id=request.user.id)  # Show only the logged-in user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


   



@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'phone', 'user__email', 'actions_column']
    # list_filter = ['user__username','user__email']
    search_fields = ['user__username', 'user__email', 'phone']
    
    
    def actions_column(self, obj):
        # Debugging: Check if obj.id is valid
        if not obj.id:
            return "No ID"
        
        try:
            # Generate the URL for the change page (view action)
            change_url = reverse("admin:SportMeetApp_customerprofile_change", args=[obj.id])
            # Generate the URL for the delete page (delete action)
            delete_url = reverse("admin:SportMeetApp_customerprofile_delete", args=[obj.id])
            
            # Material icons for "visibility" and "delete"
            eye_icon = '<span class="material-symbols-outlined">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if not request.user.is_superuser:  # Only filter for non-admin users
                kwargs["queryset"] = User.objects.filter(id=request.user.id)  # Show only the logged-in user
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
            eye_icon = '<span class="material-symbols-outlined">visibility</span>'
            delete_icon = '<span class="material-symbols-outlined">delete</span>'
            
            # Wrap the icons in links to the respective pages
            view_link = format_html('<a href="{}" class="action-icon" title="View">{}</a>', change_url, format_html(eye_icon))
            delete_link = format_html('<a href="{}" class="action-icon" title="Delete">{}</a>', delete_url, format_html(delete_icon))
            
            # Combine both links into a single cell
            return format_html('{} {}', view_link, delete_link)
        except NoReverseMatch:
            # Handle the case where the URL pattern is not found
            return "Invalid URL"

    actions_column.short_description = mark_safe(
        '<a href="#" onclick="return false;">Actions</a>'
    ) 
    
# Unregister the default User model
admin.site.unregister(User)

# Register the custom UserAdmin
admin.site.register(User, CustomUserAdmin)




    
admin.site.register(Venue, VenueAdmin)
admin.site.register(CancellationAndRefund)
admin.site.register(VenueImage)
admin.site.register(Court,CourtAdmin)
admin.site.register(Sporttype, SportAdmin)
admin.site.register(Banner)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(VenueOwnerProfile, VenueOwnerProfileAdmin)
# admin.site.register(Coupon)
# admin.site.register(Discount)