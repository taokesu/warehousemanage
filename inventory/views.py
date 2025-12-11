from pathlib import Path
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db import transaction
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.forms import formset_factory
from django.core.exceptions import ValidationError

from .models import (
    Stock, Product, Warehouse, Supplier, Document, IncomingTransaction, 
    IncomingItem, OutgoingTransaction, OutgoingItem, Client
)
from .forms import (
    IncomingDocForm, IncomingItemForm, OutgoingDocForm, OutgoingItemForm, CustomAuthenticationForm
)
from .utils import render_to_pdf


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if hasattr(user, 'role') and user.role is not None:
                if user.role.role_name == 'Менеджер':
                    return reverse_lazy('dashboard')
                elif user.role.role_name == 'Кладовщик':
                    return reverse_lazy('storekeeper_dashboard')
        return reverse_lazy('permission_denied')

@login_required
def stock_list(request):
    stocks = Stock.objects.select_related('product', 'warehouse').all()
    return render(request, 'inventory/stock_list.html', {'stocks': stocks})


@login_required
def incoming_transaction_view(request):
    ItemFormSet = formset_factory(IncomingItemForm, extra=1) # extra=1 - одна пустая форма по умолчанию

    if request.method == 'POST':
        doc_form = IncomingDocForm(request.POST)
        item_formset = ItemFormSet(request.POST, prefix='items')

        if doc_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    doc = Document.objects.create(
                        staff=request.user, 
                        document_type=Document.DocumentType.INCOMING
                    )
                    incoming_trans = doc_form.save(commit=False)
                    incoming_trans.document = doc
                    incoming_trans.save()

                    total_amount = 0
                    for item_form in item_formset:
                        if item_form.cleaned_data: # Проверяем, что форма не пустая
                            item = item_form.save(commit=False)
                            item.incoming_transaction = incoming_trans
                            item.save()
                            total_amount += item.line_total_purchase
                    
                    incoming_trans.total_amount = total_amount
                    incoming_trans.save()

                return redirect('document_list')
            except Exception as e:
                doc_form.add_error(None, f"Произошла ошибка при обработке транзакции: {e}")
    else:
        doc_form = IncomingDocForm()
        item_formset = ItemFormSet(prefix='items')

    context = {
        'doc_form': doc_form,
        'item_formset': item_formset,
        'form_title': 'Новый приходный документ',
        'form_action': reverse_lazy('incoming_transaction')
    }
    return render(request, 'inventory/transaction_form.html', context)


@login_required
def outgoing_transaction_view(request):
    ItemFormSet = formset_factory(OutgoingItemForm, extra=1)

    if request.method == 'POST':
        doc_form = OutgoingDocForm(request.POST)
        item_formset = ItemFormSet(request.POST, prefix='items')

        if doc_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    doc = Document.objects.create(
                        staff=request.user,
                        document_type=Document.DocumentType.OUTGOING
                    )
                    outgoing_trans = doc_form.save(commit=False)
                    outgoing_trans.document = doc
                    outgoing_trans.save()

                    total_amount = 0
                    for item_form in item_formset:
                        if item_form.cleaned_data:
                            # Проверка остатков на складе
                            product = item_form.cleaned_data['product']
                            quantity = item_form.cleaned_data['quantity']
                            stock = Stock.objects.filter(product=product, warehouse=outgoing_trans.warehouse).first()
                            if not stock or stock.quantity < quantity:
                                raise ValidationError(f'Недостаточно товара {product.product_name} на складе {outgoing_trans.warehouse.name}.')

                            item = item_form.save(commit=False)
                            item.outgoing_transaction = outgoing_trans
                            item.save()
                            total_amount += item.line_total_selling

                    outgoing_trans.total_amount = total_amount
                    outgoing_trans.save()

                return redirect('document_list')

            except ValidationError as e:
                doc_form.add_error(None, e.messages)
            except Exception as e:
                doc_form.add_error(None, f"Произошла непредвиденная ошибка: {e}")
    else:
        doc_form = OutgoingDocForm()
        item_formset = ItemFormSet(prefix='items')

    context = {
        'doc_form': doc_form,
        'item_formset': item_formset,
        'form_title': 'Новый расходный документ',
        'form_action': reverse_lazy('outgoing_transaction')
    }
    return render(request, 'inventory/transaction_form.html', context)

@login_required
def document_list(request):
    document_list = Document.objects.select_related('staff').all().order_by('-document_date')
    paginator = Paginator(document_list, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'inventory/document_list.html', {'page_obj': page_obj})

@login_required
def document_detail(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    transaction_details = None
    items = []

    if document.document_type == Document.DocumentType.INCOMING:
        try:
            transaction_details = document.incomingtransaction
            items = transaction_details.items.select_related('product').all()
        except Document.incomingtransaction.RelatedObjectDoesNotExist:
            pass
            
    elif document.document_type == Document.DocumentType.OUTGOING:
        try:
            transaction_details = document.outgoingtransaction
            items = transaction_details.items.select_related('product').all()
        except Document.outgoingtransaction.RelatedObjectDoesNotExist:
            pass

    context = {
        'document': document,
        'transaction': transaction_details,
        'items': items,
    }
    return render(request, 'inventory/document_detail.html', context)


@login_required
def document_pdf_view(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    transaction_details = None
    items = []

    if document.document_type == Document.DocumentType.INCOMING:
        try:
            transaction_details = document.incomingtransaction
            items = transaction_details.items.select_related('product').all()
        except Document.incomingtransaction.RelatedObjectDoesNotExist:
            pass
    elif document.document_type == Document.DocumentType.OUTGOING:
        try:
            transaction_details = document.outgoingtransaction
            items = transaction_details.items.select_related('product').all()
        except Document.outgoingtransaction.RelatedObjectDoesNotExist:
            pass

    context = {
        'document': document,
        'transaction': transaction_details,
        'items': items,
    }
    
    pdf_content = render_to_pdf('inventory/pdf/document_pdf.html', context)
    
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"document_{document.pk}_{document.document_date.strftime('%Y-%m-%d')}.pdf"
        response['Content-Disposition'] = f"attachment; filename='{filename}'"
        return response
    
    return HttpResponse("Ошибка при генерации PDF.", status=500)
