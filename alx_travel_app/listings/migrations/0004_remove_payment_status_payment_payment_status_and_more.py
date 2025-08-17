import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid

def fix_payment_data(apps, schema_editor):
    Payment = apps.get_model('listings', 'Payment')
    Booking = apps.get_model('listings', 'Booking')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    # Create a default user if none exists
    default_user = User.objects.first()
    if not default_user:
        default_user = User.objects.create(
            user_id=uuid.uuid4(),
            email="default@example.com",
            username="defaultuser",
            first_name="Default",
            last_name="User",
            role="ADMIN",
            password="pbkdf2_sha256$260000$default$default$"
        )
    for payment in Payment.objects.all():
        try:
            # Validate booking_id as UUID
            if payment.booking_id:
                uuid.UUID(str(payment.booking_id))
        except (ValueError, AttributeError):
            # Link to a default Booking or delete
            booking = Booking.objects.first()
            if booking:
                payment.booking = booking
            else:
                payment.delete()
        # Set user if missing
        payment.user = default_user
        payment.save()

class Migration(migrations.Migration):
    dependencies = [('listings', '0003_listing_watchlist')]
    operations = [
        migrations.RunPython(fix_payment_data, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(model_name='Payment', name='status'),
        migrations.AddField(
            model_name='Payment',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('COMPLETED', 'Completed'),
                    ('FAILED', 'Failed'),
                    ('REFUNDED', 'Refunded')  # Added REFUNDED
                ],
                default='PENDING',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='Payment',
            name='user',
            field=models.ForeignKey(
                default=uuid.uuid4,  # Use callable for UUID
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payments',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='Payment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='Booking',
            name='guest',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='bookings',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='Booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('CONFIRMED', 'Confirmed'),
                    ('CANCELED', 'Canceled'),
                    ('DECLINED', 'Declined'),
                    ('COMPLETED', 'Completed')
                ],
                default='PENDING',
                max_length=20  # Fixed to match enum
            ),
        ),
        migrations.AlterField(
            model_name='Listing',
            name='host',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='listings',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='Payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='Payment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='PropertyFeature',
            name='listing',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='amenities',
                to='listings.listing'
            ),
        ),
        migrations.AlterField(
            model_name='PropertyFeature',
            name='name',
            field=models.CharField(
                choices=[
                    ('WI-FI', 'wi-fi'),
                    ('POOL', 'Swimming Pool'),
                    ('PETS', 'Pets Allowed'),
                    ('GYM', 'Gym'),
                    ('PARKING', 'Parking')
                ],
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='Review',
            name='reviewer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reviews',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='Users',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
        migrations.AddIndex(
            model_name='Booking',
            index=models.Index(
                fields=['listing', 'start_date', 'end_date'],
                name='listings_bo_listing_8c812a_idx'
            ),
        ),
        migrations.AddConstraint(
            model_name='Booking',
            constraint=models.UniqueConstraint(
                fields=('listing', 'start_date', 'end_date'),
                name='unique_booking_per_date'
            ),
        ),
        migrations.AddConstraint(
            model_name='Review',
            constraint=models.UniqueConstraint(
                fields=('listing', 'reviewer'),
                name='unique_review_per_user'
            ),
        ),
    ]