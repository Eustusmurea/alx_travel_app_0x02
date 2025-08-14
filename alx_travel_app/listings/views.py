from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg

from .models import Listing, Booking, Review # Import Review for average rating calculation
from .serializers import (
    ListingSerializer,
    BookingSerializer,
    ReviewSerializer ,
    UserSerializer
)
from .enums import BookingStatus # Import BookingStatus for setting default status
from django.contrib.auth import get_user_model

User = get_user_model()

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ListingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing Listing instances.
    Provides CRUD operations for listings.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow authenticated users to write, others to read

    def perform_create(self, serializer):
        """
        Set the host of the listing to the authenticated user.
        """
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_watchlist(self, request, pk=None):
        """
        Allows an authenticated user to add a listing to their watchlist.
        """
        listing = self.get_object()
        user = request.user
        
        if user in listing.watchlist.all():
            return Response({'detail': 'Listing already in watchlist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        listing.watchlist.add(user)
        return Response({'detail': 'Listing added to watchlist.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_from_watchlist(self, request, pk=None):
        """
        Allows an authenticated user to remove a listing from their watchlist.
        """
        listing = self.get_object()
        user = request.user

        if user not in listing.watchlist.all():
            return Response({'detail': 'Listing not in watchlist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        listing.watchlist.remove(user)
        return Response({'detail': 'Listing removed from watchlist.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get all reviews for a specific listing.
        """
        listing = self.get_object()
        reviews = listing.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def book(self, request, pk=None):
        """
        Allows an authenticated user to book a specific listing.
        """
        listing = self.get_object()
        # You can get start_date and end_date from request.data
        data = request.data.copy()
        data['listing'] = listing.pk # Ensure listing ID is set
        data['guest'] = request.user.pk # Ensure guest ID is set to the current user

        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            serializer.save(listing=listing, guest=request.user, status=BookingStatus.PENDING)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing Booking instances.
    Provides CRUD operations for bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can manage bookings

    def get_queryset(self):
        """
        Optionally restrict bookings to those created by the requesting user
        or listings hosted by the requesting user.
        For hosts: see bookings for their listings.
        For guests: see their own bookings.
        """
        user = self.request.user
        if user.is_staff: # Admins can see all bookings
            return Booking.objects.all()
        # Guests can see their own bookings
        # Hosts can see bookings for their listings
        return Booking.objects.filter(guest=user) | Booking.objects.filter(listing__host=user)

    def perform_create(self, serializer):
        """
        Set the guest of the booking to the authenticated user and initial status.
        The `BookingSerializer`'s `create` method already handles total_price calculation.
        """
        # The serializer handles `guest` from validated_data already if passed.
        # Ensure it's explicitly set to the requesting user for security.
        serializer.save(guest=self.request.user, status=BookingStatus.PENDING)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Allows a host to approve a pending booking.
        """
        booking = self.get_object()
        user = request.user

        # Only the host of the listing associated with the booking can approve
        if booking.listing.host != user:
            return Response({'detail': 'You are not authorized to approve this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        if booking.status != BookingStatus.PENDING:
            return Response({'detail': 'Booking is not pending and cannot be approved.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def decline(self, request, pk=None):
        """
        Allows a host to decline a pending booking.
        """
        booking = self.get_object()
        user = request.user

        # Only the host of the listing associated with the booking can decline
        if booking.listing.host != user:
            return Response({'detail': 'You are not authorized to decline this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return Response({'detail': 'Booking is already cancelled or completed.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.DECLINED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Allows the guest who made the booking, or the host, to cancel a booking.
        """
        booking = self.get_object()
        user = request.user

        # Check if the user is the guest or the host of the listing
        if booking.guest != user and booking.listing.host != user:
            return Response({'detail': 'You are not authorized to cancel this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.DECLINED]:
            return Response({'detail': 'Booking cannot be cancelled from its current status.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.CANCELLED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)