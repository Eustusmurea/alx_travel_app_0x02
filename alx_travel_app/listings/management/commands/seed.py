from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker
import random
from decimal import Decimal

# Import your models
from listings.enums import AMENITIES, Roles
from listings.models import Users, Listing, PropertyFeature, Booking, Review

fake = Faker()

class Command(BaseCommand):
    help = "Populate database with sample Airbnb-like data using Faker"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Faker population..."))

        try:
            with transaction.atomic():
                # 1. Create Admin User
                admin, created = Users.objects.get_or_create(
                    username="admin_airbnb_clone",
                    email="admin_airbnb_clone@gmail.com",
                    defaults={
                        "first_name": "Admin",
                        "last_name": "Admin",
                        "role": Roles.ADMIN,
                        "is_staff": 1,
                    },
                )
                if created:
                    admin.set_password("admin123")
                    admin.save()
                    self.stdout.write(self.style.SUCCESS("Created admin user."))

                # 2. Create Host Users
                hosts = []
                for _ in range(3):
                    host = Users.objects.create_user(
                        username=fake.user_name(),
                        email=fake.email(),
                        password="host123",
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        phone_number=fake.phone_number(),
                        role=Roles.HOST,
                    )
                    hosts.append(host)
                self.stdout.write(self.style.SUCCESS(f"Created {len(hosts)} hosts."))

                # 3. Create Guest Users
                guests = []
                for _ in range(5):
                    guest = Users.objects.create_user(
                        username=fake.user_name(),
                        email=fake.email(),
                        password="guest123",
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        role=Roles.GUEST,
                    )
                    guests.append(guest)
                self.stdout.write(self.style.SUCCESS(f"Created {len(guests)} guests."))

                # 4. Create Listings for each Host
                listings = []
                for host in hosts:
                    for _ in range(random.randint(2, 4)):
                        listing = Listing.objects.create(
                            host=host,
                            title=fake.sentence(nb_words=5),
                            description=fake.text(max_nb_chars=200),
                            location=fake.address(),
                            price_per_night=Decimal(random.randint(50, 500)),
                            is_available=True,
                        )
                        listings.append(listing)

                        # Add random amenities
                        for amenity in random.sample(list(AMENITIES), k=3):
                            PropertyFeature.objects.create(
                                listing=listing,
                                name=amenity,
                            
                            )

                        # Add watchlist (random guests)
                        listing.watchlist.add(*random.sample(guests, k=random.randint(0, 3)))

                self.stdout.write(self.style.SUCCESS(f"Created {len(listings)} listings."))

                # 5. Create Bookings
                for guest in guests:
                    for _ in range(random.randint(1, 3)):
                        listing = random.choice(listings)
                        booking = Booking.objects.create(
                            listing=listing,
                            guest=guest,
                            start_date=fake.date_between(start_date="-1y", end_date="today"),
                            end_date=fake.date_between(start_date="today", end_date="+1y"),
                            total_price=listing.price_per_night * Decimal(random.randint(1, 10)),
                        )

                        # # Add a review sometimes
                        # if random.choice([True, False]):
                        #     Review.objects.create(
                        #         listing=listing,
                        #         # guest=guest,
                        #         rating=random.randint(1, 5),
                        #         comment=fake.sentence(),
                        #     )

                self.stdout.write(self.style.SUCCESS("✅ Faker data population completed!"))

        except Exception as e:
            raise CommandError(f"Error populating data: {e}")
