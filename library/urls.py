from django.urls import path
from . import views
from .views import register
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/edit/<int:pk>/', views.edit_book, name='edit_book'),
    path('books/delete/<int:book_id>/', views.delete_book, name='delete_book'),
    path('admin-books/', views.admin_book_list, name='admin_book_list'),
    path('books/borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('borrowed_books/', views.borrowed_books, name='borrowed_books'),
    path('return_book/<int:borrow_id>/', views.return_book, name='return_book'),
    path('borrow-history/', views.borrow_history, name='borrow_history'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('register/', register, name='register'),
    path('logout/', LogoutView.as_view(next_page='book_list'), name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('admin/overdue/', views.overdue_books, name='overdue_books'),
    path('overdue/', views.overdue_books, name='overdue_books_user'),
    path('book/<int:book_id>/history/', views.book_history, name='book_history'),
    path('user/history/', views.borrow_history, name='borrow_history'),
    path('profile/', views.user_profile, name='user_profile'),





]
