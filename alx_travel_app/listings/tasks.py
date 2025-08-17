from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_payment_success_email(user_email, booking_id, amount):
    subject = "Payment Successful"
    message = f"Your payment of {amount} for booking {booking_id} was successful."
    send_mail(
        subject,
        message,
        "mwirigiustus97@gmail.com",  # From email
        [user_email],
        fail_silently=False,
    )
    return f"Email sent to {user_email}"