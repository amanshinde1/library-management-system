from django import forms
from .models import Book, Borrow

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description','available']

class BorrowForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['book','due_date']
