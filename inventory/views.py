from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views import View
from .models import (
    Document, Transaction, Inventory, Product, Warehouse
)
from .forms import IncomingTransactionForm, OutgoingTransactionForm, DocumentForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.generic import ListView
from django.db.models import Sum
from django.db import transaction as db_transaction


@login_required
def stock_list(request):
    # stocks = Stock.objects.select_related('product', 'warehouse').all()
    # context = {
    #     'stocks': stocks,
    # }
    # return render(request, 'inventory/stock_list.html', context)
    return render(request, 'inventory/stock_list.html', {'stocks': []})


@login_required
def document_list(request):
    documents = Document.objects.all().order_by('-date_created')
    return render(request, 'inventory/document_list.html', {'documents': documents})


@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    transactions = document.transactions.all().select_related('product')
    return render(request, 'inventory/document_detail.html', {
        'document': document,
        'transactions': transactions
    })


@login_required
def incoming_form_view(request):
    if request.method == 'POST':
        form = IncomingTransactionForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                document = Document.objects.create(
                    document_type='Приход',
                    user=request.user
                )
                products = form.cleaned_data['products']
                for item in products:
                    Transaction.objects.create(
                        document=document,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price'],
                        transaction_type='Приход'
                    )
            return redirect('document_list')
    else:
        form = IncomingTransactionForm()
    return render(request, 'inventory/incoming_form.html', {'form': form})


@login_required
def outgoing_form_view(request):
    if request.method == 'POST':
        form = OutgoingTransactionForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                document = Document.objects.create(
                    document_type='Расход',
                    user=request.user
                )
                products = form.cleaned_data['products']
                for item in products:
                    Transaction.objects.create(
                        document=document,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price'],
                        transaction_type='Расход'
                    )
            return redirect('document_list')
    else:
        form = OutgoingTransactionForm()
    return render(request, 'inventory/outgoing_form.html', {'form': form})


class StorekeeperDashboardView(View):
    def get(self, request, *args, **kwargs):
        total_products = Product.objects.count()
        total_quantity = Inventory.objects.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        low_stock_products = Product.objects.filter(inventory__quantity__lt=10).distinct()
        
        context = {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'low_stock_products': low_stock_products,
            'page_title': 'Панель управления кладовщика'
        }
        return render(request, 'inventory/storekeeper_dashboard.html', context)


@login_required
def document_pdf_view(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    template_path = 'inventory/document_pdf.html'
    context = {'document': document}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="document_{document.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
        html, dest=response
    )

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
