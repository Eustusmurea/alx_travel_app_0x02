from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.views.decorators.csrf import csrf_exempt

# DRF router for listings and bookings
router = DefaultRouter()
router.register(r'listings', views.ListingViewSet, basename='listing')
router.register(r'bookings', views.BookingViewSet, basename='booking')

# Payment URLs
payment_urls = [
    path('initialize/', views.InitializePaymentView.as_view(), name='initialize_payment'),
    path('verify/', views.VerifyPaymentView.as_view(), name='verify_payment'),
    path('webhook/', csrf_exempt(views.PaymentWebhookView.as_view()), name='payment_webhook'),
    path('return/', views.PaymentReturnView.as_view(), name='payment_return'),
]

# Auth URLs
auth_urls = [
    path('signup/', views.SignupView.as_view(), name='signup'),
]

# Main URL patterns
urlpatterns = [
    path('', include(router.urls)),  # listings/bookings
    path('payments/', include((payment_urls, 'payments'))),
    path('auth/', include((auth_urls, 'auth'))),
]
