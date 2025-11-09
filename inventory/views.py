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

from .models import Stock, Product, Warehouse, Supplier, Document, IncomingTransaction, IncomingItem, OutgoingTransaction, OutgoingItem, Client
from .forms import IncomingForm, OutgoingForm, CustomAuthenticationForm
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

def stock_list(request):
    stocks = Stock.objects.select_related('product', 'warehouse').all()
    return render(request, 'inventory/stock_list.html', {'stocks': stocks})

def incoming_transaction_view(request):
    if request.method == 'POST':
        form = IncomingForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            supplier = form.cleaned_data['supplier']
            warehouse = form.cleaned_data['warehouse']
            quantity = form.cleaned_data['quantity']

            try:
                with transaction.atomic():
                    doc = Document.objects.create(
                        staff=request.user, 
                        document_type=Document.DocumentType.INCOMING
                    )
                    incoming_trans = IncomingTransaction.objects.create(
                        document=doc,
                        supplier=supplier,
                        warehouse=warehouse
                    )
                    IncomingItem.objects.create(
                        incoming_transaction=incoming_trans,
                        product=product,
                        quantity=quantity
                    )
                    incoming_trans.total_amount = product.purchase_price * quantity
                    incoming_trans.save()

                return redirect('document_list')
            except Exception as e:
                form.add_error(None, f"Произошла ошибка при обработке транзакции: {e}")
    else:
        form = IncomingForm()
    return render(request, 'inventory/incoming_form.html', {'form': form})

def outgoing_transaction_view(request):
    if request.method == 'POST':
        form = OutgoingForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            client = form.cleaned_data['client']
            warehouse = form.cleaned_data['warehouse']
            quantity = form.cleaned_data['quantity']

            try:
                with transaction.atomic():
                    doc = Document.objects.create(
                        staff=request.user,
                        document_type=Document.DocumentType.OUTGOING
                    )
                    outgoing_trans = OutgoingTransaction.objects.create(
                        document=doc,
                        client=client,
                        warehouse=warehouse
                    )
                    OutgoingItem.objects.create(
                        outgoing_transaction=outgoing_trans,
                        product=product,
                        quantity=quantity
                    )
                    outgoing_trans.total_amount = product.selling_price * quantity
                    outgoing_trans.save()

                return redirect('document_list')
            except Exception as e:
                form.add_error(None, f"Произошла непредвиденная ошибка: {e}")
    else:
        form = OutgoingForm()
    return render(request, 'inventory/outgoing_form.html', {'form': form})

def document_list(request):
    document_list = Document.objects.select_related('staff').all().order_by('-document_date')
    paginator = Paginator(document_list, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'inventory/document_list.html', {'page_obj': page_obj})

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
    """
    Генерирует PDF-версию для указанного документа.
    """
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

    # ИЗМЕНЕНО: Создаем URI для файла шрифта, чтобы избежать конфликтов
    font_path = (settings.BASE_DIR / 'static' / 'fonts' / 'DejaVuSans.ttf').as_uri()

    context = {
        'document': document,
        'transaction': transaction_details,
        'items': items,
        'font_path': font_path,
    }
    
    pdf = render_to_pdf('inventory/pdf/document_pdf.html', context)
    
    if pdf:
        filename = f"document_{document.pk}_{document.document_date.strftime('%Y-%m-%d')}.pdf"
        pdf['Content-Disposition'] = f"attachment; filename='{filename}'"
        return pdf
    
    return HttpResponse("Ошибка при генерации PDF файла.", status=400)
