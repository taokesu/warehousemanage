from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """
    Функция для рендеринга HTML-шаблона в PDF-документ.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    result = BytesIO()
    
    # ИЗМЕНЕНО: Убрали link_callback, т.к. путь к шрифту передается напрямую
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), 
        dest=result
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
        
    return None
