from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Staff, Product, Supplier, Warehouse, Client

# Форма для аутентификации
class CustomAuthenticationForm(forms.Form):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise ValidationError(
                    self.get_invalid_login_error(),
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                "Этот аккаунт неактивен.",
                code='inactive',
            )

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return "Введите правильные имя пользователя и пароль. Поля чувствительны к регистру."


# Форма для операций прихода
class IncomingForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(), 
        label="Товар",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(), 
        label="Поставщик",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(), 
        label="Склад",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        min_value=1, 
        label="Количество",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


# Форма для операций расхода
class OutgoingForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(), 
        label="Товар",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(), 
        label="Клиент",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(), 
        label="Склад",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        min_value=1, 
        label="Количество",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
