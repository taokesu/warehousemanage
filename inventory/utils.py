import os
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    """
    Преобразует URI в абсолютный путь для xhtml2pdf,
    чтобы найти статические файлы (шрифты, CSS, изображения).
    """
    # uri, который передает xhtml2pdf, может начинаться с /
    # например, /static/fonts/DejaVuSans.ttf
    sUrl = settings.STATIC_URL # 'static/'

    # ИЗМЕНЕНО: Более надежный способ получить относительный путь
    # Удаляем и /static/, и static/
    if uri.startswith(sUrl):
        static_path = uri.replace(sUrl, "")
    else:
        static_path = uri.lstrip('/')
        if static_path.startswith(sUrl):
            static_path = static_path.replace(sUrl, "")

    # Ищем абсолютный путь к файлу с помощью Django
    result = finders.find(static_path)

    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        path = result[0]
        return path
    
    return uri

def render_to_pdf(template_src, context_dict={}):
    """
    Функция для рендеринга HTML-шаблона в PDF-документ.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    result = BytesIO()
    
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), 
        dest=result,
        link_callback=link_callback
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
        
    return None
