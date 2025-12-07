from django import forms
from .models import Product, Warehouse

class ProductForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Продукт")
    quantity = forms.IntegerField(min_value=1, label="Количество")
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="Цена за единицу")

class BaseProductFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        # Здесь можно добавить дополнительную логику валидации для всего набора форм

ProductFormSet = forms.formset_factory(ProductForm, formset=BaseProductFormSet, extra=1)

class IncomingTransactionForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label="Склад")
    products = ProductFormSet

class OutgoingTransactionForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label="Склад")
    products = ProductFormSet

class DocumentForm(forms.Form):
    # Эта форма может быть не нужна, если документы создаются автоматически
    pass
