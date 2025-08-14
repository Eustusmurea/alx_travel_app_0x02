from django.db import models
from .enums import Roles, BookingStatus, AMENITIES , PaymentStatus
from django.db.models import CheckConstraint, Q, F
from django.contrib.auth.models import AbstractUser
import uuid


class Users(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    role = models.CharField(max_length=10, null=False, choices=Roles.choices, default=Roles.GUEST)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)  
    email = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=128, null=False)  
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return "No name"
    
    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")


class Listing(models.Model):
    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    host = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='listing_host')
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} listed by: {self.host_id.full_name}"

    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")


class PropertyFeature(models.Model):
    amenity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='amenity')
    name= models.CharField(max_length=10, null=False, choices=AMENITIES.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")


class Booking(models.Model):
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='customer')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=15, decimal_places=2,  null=True)
    status = models.CharField(max_length=10, null=False, choices=BookingStatus.choices, default=BookingStatus.PENDING) 
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            CheckConstraint(
                check = Q(end_date__gt=F('start_date')), 
                name = 'check_start_date',
            ),
        ]

    def __str__(self):
        return f'{self.guest.full_name} booked for {self.listing.title}'
    
    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")


class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='customer_review')
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
            constraints = [
                CheckConstraint(
                    check=Q(rating__gte=1) & Q(rating__lte=5),
                    name='rating_range_check',
                ),
            ]
    
    def __str__(self):
        return f'{self.reviewer.full_name}, rating: {self.rating} out of 5'
    
    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")   

#payment model 
#to contain payment information for bookings
#needs (Booking reference fk Booking, transaction_id, amount, status default Pending, created_at: autoadd now)

class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, null=False, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.payment_id} for {self.booking.listing.title}'

    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%b %d, %Y, %H:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")
