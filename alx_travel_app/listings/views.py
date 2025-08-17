from asyncio.log import logger
import logging
from time import time
import uuid
from django.shortcuts import render
import requests
from .chapa_service import initialize_payment, verify_payment
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404



from .models import Listing, Booking, Payment, Review # Import Review for average rating calculation
from .serializers import (
    ListingSerializer,
    BookingSerializer,
    PaymentSerializer,
    ReviewSerializer,
    UserSerializer,
    PaymentInitSerializer,
    PaymentVerifySerializer
)
from .enums import BookingStatus, PaymentStatus 
from django.contrib.auth import get_user_model

User = get_user_model()

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny] 


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
        listing = self.get_object()
        serializer = BookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(listing=listing, guest=request.user)
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

class InitializePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_id = serializer.validated_data['booking_id']
        amount = serializer.validated_data['amount']

        booking = get_object_or_404(Booking, booking_id=booking_id)
        if booking.guest != request.user:
            return Response({"error": "You are not authorized to pay for this booking"}, status=status.HTTP_403_FORBIDDEN)

        tx_ref = str(uuid.uuid4())
        response = initialize_payment(
            amount=amount,
            email=request.user.email,
            tx_ref=tx_ref,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            currency="KES"  # Adjust as needed
        )

        if response.get("status") == "success":
           with transaction.atomic(): 
            payment = Payment.objects.create(
                user=request.user,
                booking=booking,
                amount=amount,
                transaction_id=tx_ref,
                payment_status=PaymentStatus.PENDING  # Use enum
            )
            return Response({
                "checkout_url": response["data"]["checkout_url"],
                "payment": PaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED)

        return Response({"error": response.get("message", "Payment initialization failed")}, status=status.HTTP_400_BAD_REQUEST)


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx_ref = serializer.validated_data['tx_ref']
        payment = Payment.objects.filter(transaction_id=tx_ref).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if payment.user != request.user and payment.booking.listing.host != request.user:
            return Response({"error": "You are not authorized to verify this payment"}, status=status.HTTP_403_FORBIDDEN)

        response = verify_payment(tx_ref)
        if response.get("status") != "success":
            payment.payment_status = PaymentStatus.FAILED
            payment.save()
            return Response({"error": response.get("message", "Payment verification failed")}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment.payment_status = PaymentStatus.SUCCESS if response["data"].get("status") == "success" else PaymentStatus.FAILED
            payment.save()
            if payment.payment_status == PaymentStatus.SUCCESS:
                payment.booking.status = BookingStatus.CONFIRMED
                payment.booking.save()

        return Response({
            "payment": PaymentSerializer(payment).data,
            "message": "Payment verified successfully"
        }, status=status.HTTP_200_OK)
    
class ChapaWebhookView(APIView):
    permission_classes = [AllowAny]  # Secure with a secret key

    def post(self, request):
        tx_ref = request.data.get('tx_ref')
        status = request.data.get('status')
        payment = Payment.objects.filter(transaction_id=tx_ref).first()
        if not payment:
            logger.error(f"Webhook: Payment not found for tx_ref={tx_ref}")
            return Response(status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            payment.payment_status = PaymentStatus.SUCCESS if status == "success" else PaymentStatus.FAILED
            payment.save()
            if payment.payment_status == PaymentStatus.SUCCESS:
                payment.booking.status = BookingStatus.CONFIRMED
                payment.booking.save()

        logger.info(f"Webhook: Payment {tx_ref} updated to {payment.payment_status}")
        return Response(status=status.HTTP_200_OK)