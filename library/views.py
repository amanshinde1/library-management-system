from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta

from .models import Book, Borrow
from .forms import BookForm


# ✅ Book Views

def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})


@staff_member_required
def admin_book_list(request):
    books = Book.objects.all()
    return render(request, 'library/admin_book_list.html', {'books': books})


@staff_member_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully!')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/add_book.html', {'form': form})


@staff_member_required
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('admin_book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/edit_book.html', {'form': form})


@staff_member_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    messages.success(request, "Book deleted successfully.")
    return redirect('book_list')


# ✅ Borrow Views

@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.available:
        messages.warning(request, "Sorry, this book is already borrowed.")
    else:
        due_date = timezone.now() + timedelta(days=7)
        Borrow.objects.create(
            user=request.user,
            book=book,
            borrowed_at=timezone.now(),
            due_date=due_date
        )
        book.available = False
        book.save()
        messages.success(request, f"You have successfully borrowed '{book.title}'. Due on {due_date.strftime('%Y-%m-%d')}")
    return redirect('book_list')


@login_required
def borrowed_books(request):
    active_borrows = Borrow.objects.filter(user=request.user, returned=False)
    return render(request, 'library/borrowed_books.html', {'borrows': active_borrows})


@login_required
def return_book(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.user != request.user:
        messages.error(request, "You can only return books you have borrowed.")
        return redirect('borrowed_books')

    borrow.returned = True
    borrow.book.available = True
    borrow.book.save()
    borrow.save()

    messages.success(request, f"You have returned '{borrow.book.title}' successfully.")
    return redirect('borrowed_books')


@login_required
def borrow_history(request):
    user_history = Borrow.objects.filter(user=request.user).order_by('-borrowed_at')
    return render(request, 'library/borrow_history.html', {'history': user_history})


# ✅ Admin Dashboard

@staff_member_required
def admin_dashboard(request):
    total_books = Book.objects.count()
    total_borrowed = Borrow.objects.filter(returned=False).count()
    total_available = Book.objects.filter(available=True).count()
    total_users = Borrow.objects.values('user').distinct().count()

    context = {
        'total_books': total_books,
        'total_borrowed': total_borrowed,
        'total_available': total_available,
        'total_users': total_users,
    }
    return render(request, 'library/admin_dashboard.html', context)


# ✅ Registration

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('book_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# ✅ User Profile

@login_required
def user_profile(request):
    borrowed = Borrow.objects.filter(user=request.user)
    total_borrowed = borrowed.count()

    return render(request, 'library/user_profile.html', {
        'user': request.user,
        'borrowed_books': borrowed,
        'total_borrowed': total_borrowed,
    })


# ✅ Overdue Books

@staff_member_required
def overdue_books(request):
    overdue = Borrow.objects.filter(returned=False, due_date__lt=timezone.now())
    return render(request, 'library/overdue_books.html', {'overdue': overdue})


# ✅ Book History

@staff_member_required
def book_history(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    borrow_history = Borrow.objects.filter(book=book)

    return render(request, 'library/book_history.html', {
        'book': book,
        'borrow_history': borrow_history
    })
