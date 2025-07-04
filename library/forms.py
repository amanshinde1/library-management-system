from django import forms
from django.contrib.auth.models import User
from .models import Book, Borrow, Reader, UserProfile
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
import re

from .models import UserProfile

from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'genre', 'available']


class BorrowForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['book', 'due_date']


class ReaderForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = ['name', 'contact', 'reference_id', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_id': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class EditProfileForm(forms.ModelForm):
    username = forms.CharField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['phone', 'address']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

        self.user = user

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = self.user

        user.username = self.cleaned_data.get('username')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()
            profile.user = user
            profile.save()
        return profile


class UserForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('Email address must be unique.')
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not re.match(r'^[A-Za-z\s\-]+$', first_name):
            raise ValidationError("First name can only contain letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not re.match(r'^[A-Za-z\s\-]+$', last_name):
            raise ValidationError("Last name can only contain letters.")
        return last_name


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = UserProfile
        fields = ['phone', 'address']


class CustomPasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 or password2:
            # Only check if at least one password field is filled
            if password1 != password2:
                raise ValidationError("The new passwords do not match.")

            # Validate password strength only if password1 is not empty
            try:
                password_validation.validate_password(password1, self.user)
            except ValidationError as e:
                self.add_error('new_password1', e)

        return cleaned_data

class CaptchaAuthenticationForm(AuthenticationForm):
    captcha = CaptchaField()
