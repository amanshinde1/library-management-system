from django.core.mail import send_mail
from django.conf import settings

def send_borrow_notification(user_email, book_title, due_date):
    subject = f"Borrow Confirmation: {book_title}"
    message = f"You have successfully borrowed '{book_title}'. It is due on {due_date.strftime('%Y-%m-%d')}."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])

def send_return_notification(user_email, book_title):
    subject = f"Return Confirmation: {book_title}"
    message = f"You have successfully returned '{book_title}'. Thanks for using the library!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])

def send_notification_email(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False
    )