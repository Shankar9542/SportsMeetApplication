from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CustomerProfile, VenueOwnerProfile , Court,Venue

class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class VenueOwnerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        
        
class CourtForm(forms.ModelForm):
    court_count = forms.IntegerField(min_value=1, initial=1, help_text="Enter the number of courts to create.")

    class Meta:
        model = Court
        fields = ["venue", "sport", "court_number", "price", "duration"]

    def clean_court_count(self):
        court_count = self.cleaned_data.get("court_count")
        if court_count < 1:
            raise forms.ValidationError("Court count must be at least 1.")
        return court_count
    
class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'description', 'address', 'city', 'area', 'google_maps_link', 'end_date', 'start_time', 'end_time', 'image']