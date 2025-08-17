from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView,
    ListingViewSet,
    BookingViewSet,
    InitializePaymentView,
    VerifyPaymentView,
    ChapaWebhookView,
    RefundPaymentView  # Optional, included for completeness
)

# Create a router for ViewSet routes
router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

# Define explicit URL patterns
urlpatterns = [
    # User signup
    path('signup/', SignupView.as_view(), name='signup'),

    # Payment endpoints
    path('payments/init/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/webhook/', ChapaWebhookView.as_view(), name='chapa-webhook'),
  # Optional

    # Include ViewSet routes (listings/, bookings/, and custom actions)
    path('', include(router.urls)),
]