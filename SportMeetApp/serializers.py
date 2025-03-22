# serializers.py
from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from rest_framework import serializers
from django.core.mail import send_mail
from .utils.email_utils import send_verification_email


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone", "password", "confirm_password"]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already taken.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        phone = data.get("phone", "")
        if not phone.isdigit() or len(phone) != 9:
            raise serializers.ValidationError({"phone": "Phone number must be exactly 9 digits."})
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        phone = validated_data.pop('phone')
        validated_data.pop('confirm_password')

        validated_data['is_active'] = False  # User needs email verification
        validated_data['is_staff'] = True
        user = User.objects.create_user(**validated_data)
        user.save()

        # Create a customer profile
        CustomerProfile.objects.create(user=user, phone=f"+61{phone}")

        # Create email verification token
        token = EmailVerificationToken.objects.create(user=user)

        # Send email verification
        send_verification_email(request,user, token.token)

        return user

class VenueOwnerRegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password", "confirm_password"]

    def validate(self, data):
        """Validate passwords, username, email, and phone number."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Username already taken."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already registered."})

        phone = data.get("phone", "")
        if not phone.isdigit() or len(phone) != 9:
            raise serializers.ValidationError({"phone": "Phone number must be exactly 9 digits."})

        return data

    def create(self, validated_data):
        """Create user and venue owner profile."""
        request = self.context.get("request")
        phone = validated_data.pop('phone')
        validated_data.pop('confirm_password')

        validated_data['is_active'] = False  # Needs email verification
        validated_data['is_staff'] = True  # Owners are staff

        user = User.objects.create_user(**validated_data)
        user.save()
        
        # Save phone number with +61 prefix in backend
        VenueOwnerProfile.objects.create(user=user, phone=f"+61{phone}")

        # Create email verification token
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email(request,user, token.token)

        return user
       

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]



class SporttypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sporttype
        fields = ['id', 'name', 'image']

class VenueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueImage
        fields = ['image']
        
class ReviewSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)  # Display customer's name
    owner_reply = serializers.CharField(read_only=True)  # Read-only reply field

    class Meta:
        model = Rating
        fields = ['id', 'customer', 'rating', 'review','owner_reply', 'replied_at', 'created_at']
 
        
class VenueSerializer(serializers.ModelSerializer):
    images = VenueImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    class Meta:
        model = Venue
        fields = '__all__'
        
    def get_average_rating(self, obj):
        return obj.average_rating()
        
class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'court_no', 'price']
        

      

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'customer', 'venue', 'sport', 'court', 'date', 'start_time', 'end_time', 'price', 'booking_status', 'mode_of_payment']

    