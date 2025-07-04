from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views
from .views import export_readers_csv
from .forms import CaptchaAuthenticationForm

urlpatterns = [
    path('', views.landing_page, name='landing_page'),  # Home page with login/register links

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

    path('register/', views.register, name='register'),


    path('logout/', auth_views.LogoutView.as_view(), name='logout'),


    path('profile/', views.user_profile, name='user_profile'),
    path('admin/overdue/', views.overdue_books, name='overdue_books'),
    path('overdue/', views.overdue_books, name='overdue_books_user'),
    path('book/<int:book_id>/history/', views.book_history, name='book_history'),
    path('user/history/', views.borrow_history, name='borrow_history'),
    path('my-bag/', views.my_bag, name='my_bag'),
    path('add-to-bag/<int:book_id>/', views.add_to_bag, name='add_to_bag'),
    path('remove-from-bag/<int:book_id>/', views.remove_from_bag, name='remove_from_bag'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('readers/', views.reader_list, name='reader_list'),
    path('readers/add/', views.add_reader, name='add_reader'),
    path('readers/edit/<int:pk>/', views.edit_reader, name='edit_reader'),
    path('readers/delete/<int:pk>/', views.delete_reader, name='delete_reader'),
    path('pay-fine/<int:borrow_id>/', views.pay_fine, name='pay_fine'),
    path('readers/export/', export_readers_csv, name='export_readers_csv'),
    path('readers/<int:pk>/', views.reader_detail, name='reader_detail'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('captcha/', include('captcha.urls')),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        authentication_form=CaptchaAuthenticationForm
    ), name='login'),








]
