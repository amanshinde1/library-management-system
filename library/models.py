from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


# BOOK MODEL
class Book(models.Model):
    GENRE_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('mystery', 'Mystery'),
        ('sci-fi', 'Sci-Fi'),
        ('biography', 'Biography'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='other')  # ✅ New field
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# BORROW MODEL
class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # revert back to required
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)
    fine_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} borrowed {self.book}"

    @property
    def is_overdue(self):
        return not self.returned and self.due_date and timezone.now() > self.due_date

    @property
    def fine_amount(self):
        if not self.is_overdue:
            return 0
        fine_rate_per_day = 10
        days_overdue = (timezone.now() - self.due_date).days
        return fine_rate_per_day * days_overdue


# BORROW HISTORY MODEL
class BorrowHistory(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
    ], default='borrowed')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"


# READER MODEL
class Reader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    reference_id = models.CharField(max_length=50)
    address = models.TextField()

    def __str__(self):
        return self.name


# USER PROFILE MODEL
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        try:
            instance.userprofile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
