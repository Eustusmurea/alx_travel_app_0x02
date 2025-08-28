# airbnb_app/serializers.py

from decimal import Decimal
from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review, Payment
from .enums import Roles, BookingStatus
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom Users model."""
    full_name = serializers.ReadOnlyField()
    formatted_created_at = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Users
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'full_name', 'formatted_created_at',
            'password',
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name', 'formatted_created_at']

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Users.objects.create_user(**validated_data)
        user.set_password(password)  # hash properly
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class PropertyFeatureSerializer(serializers.ModelSerializer):
    """Serializer for PropertyFeature model (amenities)."""
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = PropertyFeature
        fields = [
            'amenity_id', 'listing', 'name',
            'created_at', 'formatted_created_at'
        ]
        read_only_fields = ['amenity_id', 'created_at', 'formatted_created_at']
        extra_kwargs = {
            'listing': {'write_only': True}
        }


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    reviewer_full_name = serializers.ReadOnlyField(source='reviewer.full_name')
    listing_title = serializers.ReadOnlyField(source='listing.title')
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = [
            'review_id', 'listing', 'reviewer', 'rating', 'comment',
            'created_at', 'reviewer_full_name', 'listing_title',
            'formatted_created_at'
        ]
        read_only_fields = [
            'review_id', 'created_at', 'reviewer_full_name',
            'listing_title', 'formatted_created_at'
        ]
        extra_kwargs = {
            'listing': {'write_only': True},
            'reviewer': {'write_only': True}
        }

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for the Listing model."""
    host = UserSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    watchlist = UserSerializer(many=True, read_only=True)
    formatted_created_at = serializers.ReadOnlyField()
    interested_clients = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'listing_id', 'host', 'title', 'description', 'location',
            'price_per_night', 'is_available', 'watchlist', 'created_at',
            'updated_at', 'reviews', 'formatted_created_at',
            'interested_clients', 'average_rating'
        ]
        read_only_fields = [
            'listing_id', 'host', 'created_at', 'updated_at'
        ]

    def get_interested_clients(self, obj):
        return [user.full_name for user in obj.watchlist.all()]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return "No Review"
        return round(sum([r.rating for r in reviews]) / len(reviews), 1)


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for the Booking model."""
    listing_detail = ListingSerializer(source='listing', read_only=True)
    guest_detail = UserSerializer(source='guest', read_only=True)
    formatted_created_at = serializers.ReadOnlyField()
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'listing', 'guest', 'start_date', 'end_date',
            'total_price', 'status', 'created_at', 'formatted_created_at',
            'listing_detail', 'guest_detail'
        ]
        read_only_fields = [
            'booking_id', 'created_at', 'formatted_created_at',
            'total_price', 'status'
        ]

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        listing = data.get('listing')

        if end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date.")

        if Booking.objects.filter(
            listing=listing,
            start_date__lt=end_date,
            end_date__gt=start_date,
            status__in=['pending', 'confirmed']
        ).exists():
            raise serializers.ValidationError("This listing is already booked for part or all of the selected dates.")

        return data

    def create(self, validated_data):
        listing = validated_data['listing']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        duration_days = (end_date - start_date).days

        if duration_days <= 0:
            raise serializers.ValidationError("Booking duration must be at least one day.")

        validated_data['total_price'] = Decimal(duration_days) * listing.price_per_night
        validated_data['status'] = BookingStatus.PENDING

        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class PaymentInitSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaymentVerifySerializer(serializers.Serializer):
    tx_ref = serializers.CharField()
