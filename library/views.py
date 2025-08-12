import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Book, Borrow, BorrowHistory, Reader, UserProfile
from .forms import BookForm, BorrowForm, ReaderForm, UserUpdateForm, EditProfileForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserForm, UserProfileForm, CustomPasswordChangeForm

from django.http import HttpResponseRedirect
from django.urls import reverse

from django.http import HttpResponse
from .utils.email_utils import send_notification_email

from django.db.models import Count


from library.utils.email_utils import send_borrow_notification




def landing_page(request):
    return render(request, 'landing.html')


# Book Views
def book_list(request):
    books = Book.objects.all()

    # Search and filters
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '')
    availability = request.GET.get('available', '')

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if genre:
        books = books.filter(genre=genre)
    if availability == 'available':
        books = books.filter(available=True)
    elif availability == 'unavailable':
        books = books.filter(available=False)

    books = books.order_by('title')

    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    borrowed_book_ids = []
    borrowed_books = []
    if request.user.is_authenticated:
        borrowed_books = Borrow.objects.filter(user=request.user, returned=False)
        borrowed_book_ids = [b.book.id for b in borrowed_books]

    context = {
        'page_obj': page_obj,
        'query': query,
        'genre': genre,
        'availability': availability,
        'borrowed_book_ids': borrowed_book_ids,
        'active_borrows': borrowed_books,
        'genres': Book.GENRE_CHOICES,
    }
    return render(request, 'library/book_list.html', context)



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


# Borrow Views
@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.available:
        messages.warning(request, "Sorry, this book is already borrowed.")
    else:
        due_date = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(
            user=request.user,
            book=book,
            borrowed_at=timezone.now(),
            due_date=due_date
        )
        book.available = False
        book.save()
        messages.success(request, f"You have successfully borrowed '{book.title}'. Due on {due_date.strftime('%Y-%m-%d')}")

        # Send email notification
        subject = f"Book Borrowed: {book.title}"
        message = f"Hi {request.user.username},\n\nYou borrowed '{book.title}'. Please return it by {due_date.strftime('%Y-%m-%d')}.\n\nThank you!"
        send_notification_email(subject, message, [request.user.email])

    return redirect('book_list')



@login_required
def borrowed_books(request):
    active_borrows = Borrow.objects.filter(user=request.user, returned=False)
    return render(request, 'library/borrowed_books.html', {
        'borrows': active_borrows,
        'today': timezone.now().date()
    })



@login_required
def return_book(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user, returned=False)

    if request.method == 'POST':
        borrow.returned = True
        borrow.returned_at = timezone.now()
        borrow.book.available = True
        borrow.book.save()
        borrow.save()

        # Send email notification on return
        subject = f"Book Returned: {borrow.book.title}"
        message = f"Hi {request.user.username},\n\nYou have successfully returned '{borrow.book.title}'. Thank you!"
        send_notification_email(subject, message, [request.user.email])

        messages.success(request, f"You have returned '{borrow.book.title}'. Thank you!")
        return redirect('book_list')

    return render(request, 'library/confirm_return.html', {'borrow': borrow})





@login_required
def borrow_history(request):
    user_history = Borrow.objects.filter(user=request.user).order_by('-borrowed_at')
    return render(request, 'library/borrow_history.html', {'history': user_history})


# Admin Dashboard
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


# Registration
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


# User Profile
@login_required
def user_profile(request):
    borrowed = Borrow.objects.filter(user=request.user)
    total_borrowed = borrowed.count()

    return render(request, 'library/user_profile.html', {
        'user': request.user,
        'borrowed_books': borrowed,
        'total_borrowed': total_borrowed,
    })


# Overdue Books
@staff_member_required
def overdue_books(request):
    overdue = Borrow.objects.filter(returned=False, due_date__lt=timezone.now())
    return render(request, 'library/overdue_books.html', {'overdue': overdue})


# Book History View (moved from models.py)
def book_history(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    history = BorrowHistory.objects.filter(book=book).order_by('-borrow_date')
    return render(request, 'library/book_history.html', {'book': book, 'history': history})


# User History View (moved from models.py)
@login_required
def user_history(request):
    user = request.user
    history = BorrowHistory.objects.filter(user=user).order_by('-borrow_date')
    return render(request, 'library/user_history.html', {'history': history})


@staff_member_required
def book_history(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    borrow_history = Borrow.objects.filter(book=book)

    return render(request, 'library/book_history.html', {
        'book': book,
        'borrow_history': borrow_history
    })


@staff_member_required
def reader_list(request):
    query = request.GET.get('search', '').strip()
    if query:
        readers_queryset = Reader.objects.filter(
            Q(name__icontains=query) |
            Q(contact__icontains=query) |
            Q(reference_id__icontains=query)
        )
    else:
        readers_queryset = Reader.objects.all()

    paginator = Paginator(readers_queryset, 10)
    page_number = request.GET.get('page')
    readers = paginator.get_page(page_number)

    form = ReaderForm()

    return render(request, 'library/readers.html', {
        'readers': readers,
        'form': form,
        'search_query': query,
    })


# Bag Features
@login_required(login_url='/login/')
def add_to_bag(request, book_id):
    bag = request.session.get('my_bag', [])
    book_id_str = str(book_id)
    if book_id_str not in bag:
        bag.append(book_id_str)
        request.session['my_bag'] = bag
        messages.success(request, "Book added to your bag.")
    else:
        messages.info(request, "Book already in your bag.")
    return redirect('my_bag')  # Redirect to My Bag page




@login_required(login_url='/login/')
def remove_from_bag(request, book_id):
    bag = request.session.get('my_bag', [])
    book_id_str = str(book_id)
    if book_id_str in bag:
        bag.remove(book_id_str)
        request.session['my_bag'] = bag
        messages.success(request, "Book removed from your bag.")
    else:
        messages.info(request, "Book was not in your bag.")
    next_url = request.GET.get('next', 'my_bag')
    return redirect(next_url)


@login_required
def my_bag(request):
    bag = request.session.get('my_bag', [])
    bag = [int(bid) for bid in bag]
    books = Book.objects.filter(id__in=bag)
    return render(request, 'library/my_bag.html', {'books': books})


@login_required
def checkout(request):
    bag = request.session.get('my_bag', [])
    bag = [int(bid) for bid in bag]

    if not bag:
        messages.warning(request, "Your bag is empty.")
        return redirect('my_bag')

    books = Book.objects.filter(id__in=bag, available=True)
    if not books:
        messages.error(request, "No available books in your bag to borrow.")
        return redirect('my_bag')

    due_date = timezone.now() + timedelta(days=7)
    borrowed_titles = []

    for book in books:
        Borrow.objects.create(
            user=request.user,
            book=book,
            borrowed_at=timezone.now(),
            due_date=due_date,
        )
        book.available = False
        book.save()
        borrowed_titles.append(book.title)

    # ✅ Email confirmation
    subject = "Library Checkout Confirmation"
    message = (
        f"Hi {request.user.username},\n\n"
        f"You have successfully borrowed the following books:\n\n"
        + "\n".join(f"- {title}" for title in borrowed_titles) +
        f"\n\nPlease return them by {due_date.strftime('%Y-%m-%d')}.\n\n"
        "Thank you and happy reading!\nPeace Library"
    )
    send_notification_email(subject, message, [request.user.email])

    # ✅ Clear bag and show UI message
    request.session['my_bag'] = []
    messages.success(request, f"You successfully borrowed {len(books)} book(s). A confirmation email has been sent.")

    return redirect('borrowed_books')


@login_required
def edit_profile(request):
    user = request.user
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        password_form = CustomPasswordChangeForm(user, request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            if password_form.is_valid():
                # Only check current_password if password form is valid
                current_password = password_form.cleaned_data.get('current_password')
                if current_password:
                    # Update password
                    user.set_password(password_form.cleaned_data.get('new_password1'))
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Password updated successfully.")
                else:
                    # current_password missing or empty, treat as no password change
                    messages.success(request, "Profile updated successfully.")
            else:
                # Password form invalid but user/profile valid
                messages.error(request, "Please correct the errors in the password fields.")
                context = {
                    'user_form': user_form,
                    'profile_form': profile_form,
                    'password_form': password_form,
                }
                return render(request, "library/edit_profile.html", context)

            return redirect('user_profile')

        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        password_form = CustomPasswordChangeForm(user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, "library/edit_profile.html", context)



@staff_member_required
def add_reader(request):
    if request.method == 'POST':
        form = ReaderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reader added successfully!')
            return redirect('reader_list')
        else:
            messages.error(request, 'Please correct the errors below.')
            readers = Reader.objects.all()
            paginator = Paginator(readers, 10)
            page_number = request.GET.get('page')
            readers_page = paginator.get_page(page_number)
            return render(request, 'library/readers.html', {
                'readers': readers_page,
                'form': form,
                'search_query': '',
            })
    else:
        return redirect('reader_list')


@staff_member_required
def edit_reader(request, pk):
    reader = get_object_or_404(Reader, pk=pk)

    if request.method == 'POST':
        form = ReaderForm(request.POST, instance=reader)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reader updated successfully!')
            return redirect('reader_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReaderForm(instance=reader)

    return render(request, 'library/edit_reader.html', {'form': form, 'reader': reader})


@staff_member_required
def delete_reader(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    if request.method == 'POST':
        reader.delete()
        messages.success(request, 'Reader deleted successfully.')
        return redirect('reader_list')
    return render(request, 'library/confirm_delete.html', {'object': reader, 'type': 'reader'})


@login_required
def pay_fine(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)

    if borrow.fine_amount > 0 and not borrow.fine_paid:
        borrow.fine_paid = True
        borrow.save()
        messages.success(request, f"Fine of {borrow.fine_amount} has been marked as paid.")
    else:
        messages.info(request, "No fine to pay or fine already paid.")

    return HttpResponseRedirect(reverse('borrowed_books'))



@staff_member_required
def export_readers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="readers.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact', 'Reference ID', 'Address'])

    readers = Reader.objects.all()
    for reader in readers:
        writer.writerow([reader.name, reader.contact, reader.reference_id, reader.address])

    return response

@staff_member_required
def reader_detail(request, pk):
    reader = get_object_or_404(Reader, pk=pk)

    # All borrows by this reader's user
    borrows = Borrow.objects.filter(user=reader.user).order_by('-borrowed_at')

    # Separate active borrows (not returned)
    active_borrows = borrows.filter(returned=False)

    # Separate past borrows (returned)
    past_borrows = borrows.filter(returned=True)

    return render(request, 'library/reader_detail.html', {
        'reader': reader,
        'active_borrows': active_borrows,
        'past_borrows': past_borrows,
    })




@staff_member_required
def admin_reports(request):
    # Most borrowed books data
    most_borrowed_books = (
        Borrow.objects.values('book__title')
        .annotate(total=Count('book'))
        .order_by('-total')[:5]
    )
    borrowed_labels = [entry['book__title'] for entry in most_borrowed_books]
    borrowed_data = [entry['total'] for entry in most_borrowed_books]

    # Most active readers data
    most_active_readers = (
        Borrow.objects.values('user__username')
        .annotate(total=Count('user'))
        .order_by('-total')[:5]
    )
    reader_labels = [entry['user__username'] for entry in most_active_readers]
    reader_data = [entry['total'] for entry in most_active_readers]

    # Book availability data
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available=True).count()
    borrowed_books_count = total_books - available_books

    return render(request, 'library/admin_reports.html', {
        'total_books': total_books,
        'total_borrowed': borrowed_books_count,
        'total_users': Borrow.objects.values('user').distinct().count(),
        'most_borrowed_books_labels': borrowed_labels,
        'most_borrowed_books_data': borrowed_data,
        'most_active_readers_labels': reader_labels,
        'most_active_readers_data': reader_data,
        'available_books': available_books,
        'borrowed_books_count': borrowed_books_count,
    })
