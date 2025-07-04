from django.contrib import admin
from .models import Reader, Book, Borrow, BorrowHistory, UserProfile

admin.site.register(Reader)
admin.site.register(Book)
admin.site.register(Borrow)
admin.site.register(BorrowHistory)
admin.site.register(UserProfile)
