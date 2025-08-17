from django.db import models

class Roles(models.TextChoices):
    GUEST = 'GUEST', 'Guest'
    HOST = 'HOST', 'Host'
    ADMIN = 'ADMIN', 'Admin'

class BookingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELED = 'CANCELED', 'Canceled'  # Matches provided spelling
    DECLINED = 'DECLINED', 'Declined'  #
    COMPLETED = 'COMPLETED', 'Completed'
class AMENITIES(models.TextChoices):
    WI_FI = 'WI-FI', 'wi-fi'
    POOL = 'POOL', 'Swimming Pool'
    PETS = 'PETS', 'Pets Allowed' 
    GYM = "GYM", "Gym" 
    PARKING = 'PARKING', 'Parking'

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
