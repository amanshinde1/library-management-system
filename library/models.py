from django.db import models
from django.contrib.auth.models import User

#BOOKMODEL
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)


    def __str__(self):
        return self.title

#borrow
class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title}"

from django.utils import timezone

class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} borrowed {self.book}"

    @property
    def is_overdue(self):
        return not self.returned and self.due_date and timezone.now() > self.due_date

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BorrowHistory(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
    ], default='borrowed')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"
from django.shortcuts import render
from .models import Book, BorrowHistory

def book_history(request, book_id):
    book = Book.objects.get(id=book_id)
    history = BorrowHistory.objects.filter(book=book).order_by('-borrow_date')  # Fetch history for this book
    return render(request, 'library/book_history.html', {'book': book, 'history': history})
from django.shortcuts import render
from .models import BorrowHistory

def user_history(request):
    user = request.user  # Get the current logged-in user
    history = BorrowHistory.objects.filter(user=user).order_by('-borrow_date')  # Fetch the user's history
    return render(request, 'library/user_history.html', {'history': history})


