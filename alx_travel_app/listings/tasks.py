import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)

@shared_task
def send_payment_success_email(user_email, booking_id, amount):
    try:
        # Validate email format
        validate_email(user_email)
        subject = "Payment Successful"
        message = f"Your payment of {amount} for booking {booking_id} was successful."
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Payment success email sent to {user_email} for booking {booking_id}")
        return f"Email sent to {user_email}"
    except ValidationError:
        logger.error(f"Invalid email address: {user_email}")
        raise
    except ValueError as e:
        logger.error(f"Invalid input for payment email: {e}")
        raise
    except Exception as e:
        logger

@shared_task
def send_booking_confirmation_email(booking_id, user_email):
    try:
        # Validate email
        validate_email(user_email)

        subject = "Booking Confirmation"
        message = f"Your booking (ID: {booking_id}) has been confirmed. Thank you for choosing alx_travel_app!"
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Booking confirmation email sent to {user_email} for booking {booking_id}")
        return f"Email sent to {user_email}"
    except ValidationError:
        logger.error(f"Invalid email address: {user_email}")
        raise
    except ValueError as e:
        logger.error(f"Invalid input for booking confirmation email: {e}")
        raise
    except Exception as e:
        logger.error(f"Error sending booking confirmation email to {user_email}: {e}")
        raise