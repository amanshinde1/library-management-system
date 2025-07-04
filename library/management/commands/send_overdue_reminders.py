from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Borrow
from library.utils.email_utils import send_notification_email


class Command(BaseCommand):
    help = 'Send overdue book reminder emails to users'

    def handle(self, *args, **kwargs):
        overdue_borrows = Borrow.objects.filter(returned=False, due_date__lt=timezone.now())
        for borrow in overdue_borrows:
            user = borrow.user
            book = borrow.book
            due_date = borrow.due_date.strftime('%Y-%m-%d')

            subject = f"Overdue Book Reminder: {book.title}"
            message = (
                f"Hi {user.username},\n\n"
                f"The book '{book.title}' you borrowed was due on {due_date}.\n"
                "Please return it as soon as possible to avoid fines.\n\n"
                "Thank you!"
            )
            if user.email:
                send_notification_email(subject, message, [user.email])
                self.stdout.write(f"Sent overdue reminder to {user.email} for book '{book.title}'.")
            else:
                self.stdout.write(f"User {user.username} has no email set; skipping email for book '{book.title}'.")

