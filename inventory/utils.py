from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from django.conf import settings

def render_to_pdf(template_path, context_dict={}):
    """
    Рендерит HTML-шаблон в PDF с помощью WeasyPrint.
    """
    try:
        template = get_template(template_path)
        html_string = template.render(context_dict)

        response = HttpResponse(content_type='application/pdf')
        
        # WeasyPrint использует base_url для поиска статических файлов (шрифты, CSS)
        base_url = settings.BASE_DIR.as_uri() + "/"
        
        HTML(string=html_string, base_url=base_url).write_pdf(response)
        
        return response
    except Exception as e:
        # Возвращаем текстовый ответ с ошибкой для отладки
        return HttpResponse(f"Ошибка при генерации PDF: {e}", status=500)
