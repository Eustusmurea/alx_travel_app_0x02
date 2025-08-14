from rest_framework import routers

from .views import ListingViewSet, BookingViewSet

router = routers.DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)


urlpatterns = router.urls