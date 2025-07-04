from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Book, Borrow, Reader, UserProfile
from django.utils import timezone
from .forms import CustomPasswordChangeForm
from datetime import timedelta

class BookListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title='Test Book 1', author='Author 1', available=True)
        Book.objects.create(title='Test Book 2', author='Author 2', available=True)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/books/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('book_list'))
        self.assertTemplateUsed(response, 'library/book_list.html')

    def test_lists_all_books(self):
        response = self.client.get(reverse('book_list'))
        self.assertEqual(len(response.context['page_obj']), 2)

class BorrowBookTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='peace', password='testpass123')
        self.book = Book.objects.create(title='Atomic Habits', author='James Clear', genre='Self-help', available=True)
        self.borrow_url = reverse('borrow_book', args=[self.book.id])

    def test_user_can_borrow_available_book(self):
        self.client.login(username='peace', password='testpass123')
        response = self.client.get(self.borrow_url)
        self.book.refresh_from_db()
        borrow_entry = Borrow.objects.filter(user=self.user, book=self.book).first()
        self.assertRedirects(response, reverse('book_list'))
        self.assertIsNotNone(borrow_entry)
        self.assertFalse(borrow_entry.book.available)
        self.assertFalse(borrow_entry.returned)
        self.assertEqual(Borrow.objects.count(), 1)

class ReturnBookTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='peace', password='testpass123')
        self.book = Book.objects.create(title='Deep Work', author='Cal Newport', available=False)
        self.borrow = Borrow.objects.create(user=self.user, book=self.book, returned=False)
        self.return_url = reverse('return_book', args=[self.borrow.id])

    def test_user_can_return_book(self):
        self.client.login(username='peace', password='testpass123')
        response = self.client.post(self.return_url)
        self.borrow.refresh_from_db()
        self.book.refresh_from_db()
        self.assertRedirects(response, reverse('book_list'))
        self.assertTrue(self.borrow.returned)
        self.assertIsNotNone(self.borrow.returned_at)
        self.assertTrue(self.book.available)

class ReaderAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='admin', password='admin123', is_staff=True)
        self.normal_user = User.objects.create_user(username='user', password='user123')
        self.url = reverse('reader_list')

    def test_staff_can_access_reader_list(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_access_reader_list(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

class ExportReadersCSVTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='adminpass', is_staff=True)
        self.normal_user = User.objects.create_user(username='user', password='userpass')
        self.reader = Reader.objects.create(
            name="Test Reader",
            contact="1234567890",
            reference_id="REF001",
            address="Test Address",
            user=self.normal_user
        )
        self.client = Client()

    def test_admin_can_export_csv(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('export_readers_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn("Name,Contact,Reference ID,Address", content)
        self.assertIn("Test Reader", content)

    def test_non_admin_cannot_export_csv(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get(reverse('export_readers_csv'))
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [302, 403])

class CheckoutBagTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='peace', password='testpass123')
        self.book1 = Book.objects.create(title='Book 1', author='Author 1', available=True)
        self.book2 = Book.objects.create(title='Book 2', author='Author 2', available=False)

    def test_checkout_borrows_only_available_books_and_clears_bag(self):
        self.client.login(username='peace', password='testpass123')
        session = self.client.session
        session['my_bag'] = [str(self.book1.id), str(self.book2.id)]
        session.save()

        response = self.client.post(reverse('checkout'))

        self.book1.refresh_from_db()
        self.book2.refresh_from_db()

        self.assertRedirects(response, reverse('borrowed_books'))
        self.assertFalse(self.book1.available)
        self.assertFalse(self.book2.available)
        self.assertEqual(Borrow.objects.filter(user=self.user, book=self.book1).count(), 1)
        self.assertEqual(Borrow.objects.filter(user=self.user, book=self.book2).count(), 0)
        session = self.client.session
        self.assertEqual(session.get('my_bag', []), [])

class UserProfileEditTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='peace', password='testpass123', email='peace@example.com')
        self.url = reverse('edit_profile')

    def test_user_can_update_profile_info(self):
        self.client.login(username='peace', password='testpass123')
        data = {
            'username': 'peace',
            'email': 'newemail@example.com',
            'first_name': 'Peace',
            'last_name': 'User',
            'phone': '1234567890',
            'current_password': '',
            'new_password1': '',
            'new_password2': '',
        }
        response = self.client.post(self.url, data)
        self.user.refresh_from_db()
        self.assertRedirects(response, reverse('user_profile'))
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_user_can_change_password(self):
        self.client.login(username='peace', password='testpass123')
        data = {
            'username': 'peace',
            'email': 'peace@example.com',
            'first_name': '',
            'last_name': '',
            'phone': '',
            'current_password': 'testpass123',
            'new_password1': 'newstrongpass123',
            'new_password2': 'newstrongpass123',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('user_profile'))
        self.client.logout()
        login_successful = self.client.login(username='peace', password='newstrongpass123')
        self.assertTrue(login_successful)

class AdminReportsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='admin123', is_staff=True)
        self.user = User.objects.create_user(username='user', password='user123')
        self.book = Book.objects.create(title='Book Report', author='Author R', available=True)
        Borrow.objects.create(user=self.user, book=self.book, returned=False)

    def test_admin_can_view_reports(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('admin_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_books', response.context)
        self.assertIn('most_borrowed_books', response.context)
        self.assertIn('most_active_readers', response.context)

    def test_non_admin_cannot_view_reports(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('admin_reports'))
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [302, 403])

class OverdueBooksTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='staff123', is_staff=True)
        self.user = User.objects.create_user(username='user', password='user123')
        self.book = Book.objects.create(title='Overdue Book', author='Author O', available=False)
        Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now() - timedelta(days=1),
            returned=False
        )

    def test_overdue_books_view_for_staff(self):
        self.client.login(username='staff', password='staff123')
        response = self.client.get(reverse('overdue_books'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Overdue Book')

    def test_non_staff_cannot_access_overdue_books(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('overdue_books'))
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [302, 403])

class BorrowHistoryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='peace', password='testpass123')
        self.book = Book.objects.create(title='History Book', author='Author H', available=True)
        Borrow.objects.create(user=self.user, book=self.book, returned=True)

    def test_borrow_history_view(self):
        self.client.login(username='peace', password='testpass123')
        response = self.client.get(reverse('borrow_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'History Book')

class ReaderCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='staff123', is_staff=True)
        self.reader = Reader.objects.create(
            name='Reader1',
            contact='1234567890',
            reference_id='REF100',
            address='Address 1',
            user=self.staff
        )

    def test_staff_can_add_reader(self):
        self.client.login(username='staff', password='staff123')
        data = {
            'name': 'New Reader',
            'contact': '0987654321',
            'reference_id': 'REF200',
            'address': 'New Address',
            'user': self.staff.id,
        }
        response = self.client.post(reverse('add_reader'), data)
        self.assertRedirects(response, reverse('reader_list'))
        self.assertTrue(Reader.objects.filter(name='New Reader').exists())

    def test_staff_can_edit_reader(self):
        self.client.login(username='staff', password='staff123')
        data = {
            'name': 'Updated Reader',
            'contact': '1112223333',
            'reference_id': 'REF100',
            'address': 'Updated Address',
            'user': self.staff.id,
        }
        response = self.client.post(reverse('edit_reader', args=[self.reader.id]), data)
        self.assertRedirects(response, reverse('reader_list'))
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.name, 'Updated Reader')

    def test_staff_can_delete_reader(self):
        self.client.login(username='staff', password='staff123')
        response = self.client.post(reverse('delete_reader', args=[self.reader.id]))
        self.assertRedirects(response, reverse('reader_list'))
        self.assertFalse(Reader.objects.filter(id=self.reader.id).exists())
