from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """
    Функция для рендеринга HTML-шаблона в PDF-документ.

    :param template_src: Путь к HTML-шаблону.
    :param context_dict: Словарь с контекстом для шаблона.
    :return: HttpResponse с PDF-документом или None в случае ошибки.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    # Создаем байтовый поток для PDF
    result = BytesIO()
    
    # Генерируем PDF
    # Мы используем кодировку UTF-8 для поддержки кириллицы
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    # Если ошибок нет, возвращаем PDF как HTTP-ответ
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
        
    # В случае ошибки возвращаем None
    return None
