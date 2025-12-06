from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.http import HttpResponse
from inventory.models import Document, Transaction
from django.utils.dateformat import DateFormat

@login_required
def document_list(request):
    documents = Document.objects.all().order_by('-date')
    return render(request, 'inventory/document_list.html', {'documents': documents, 'page_title': 'Документы'}) 

@login_required
def document_detail(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    transactions = Transaction.objects.filter(document=document)

    total_sum = sum(item.quantity * item.price for item in transactions)

    context = {
        'document': document,
        'transactions': transactions,
        'total_sum': total_sum,
        'page_title': f'{document.document_type} №{document.id}',
        'transaction': transactions.first() 
    }

    if 'pdf' in request.GET:
        context['is_pdf'] = True
        # Форматируем дату для PDF, так как в нем могут быть проблемы с фильтрами Django
        df = DateFormat(document.date)
        context['formatted_date'] = df.format('d E Y г.')
        
        html = render_to_string('inventory/document_pdf.html', context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename="{document.document_type}_{document.id}.pdf"'
        
        from weasyprint import HTML
        HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
        
        return response

    return render(request, 'inventory/document_detail.html', context)
