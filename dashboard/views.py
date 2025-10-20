from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from inventory.models import Stock, Document, OutgoingItem, OutgoingTransaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date, timedelta
from django.http import JsonResponse

# --- Функции проверки ролей ---
def is_manager(user):
    """Проверяет, является ли пользователь Менеджером."""
    return user.is_authenticated and hasattr(user, 'role') and user.role is not None and user.role.role_name == 'Менеджер'

def is_storekeeper(user):
    """Проверяет, является ли пользователь Кладовщиком."""
    return user.is_authenticated and hasattr(user, 'role') and user.role is not None and user.role.role_name == 'Кладовщик'

# --- Декораторы для проверки прав ---
manager_required = user_passes_test(is_manager, login_url='/permission-denied/')
storekeeper_required = user_passes_test(is_storekeeper, login_url='/permission-denied/')

# --- Представления ---
@login_required
def custom_logout(request):
    """Выполняет выход пользователя и перенаправляет на страницу входа."""
    logout(request)
    return redirect('login')

def permission_denied_view(request):
    """Отображает страницу 'Доступ запрещен'."""
    return render(request, 'registration/permission_denied.html')

@login_required
@storekeeper_required
def storekeeper_dashboard_view(request):
    """Отображает рабочий стол кладовщика."""
    return render(request, 'inventory/storekeeper_dashboard.html')

@login_required
@manager_required
def dashboard_view(request):
    """Отображает главную панель для менеджера."""
    today = date.today()

    # Данные для карточек KPI
    outgoing_docs_today = OutgoingTransaction.objects.filter(document__document_date__date=today)
    sales_items_today = OutgoingItem.objects.filter(outgoing_transaction__document__document_date__date=today)

    today_revenue = sales_items_today.annotate(
        revenue=ExpressionWrapper(F('quantity') * F('product__selling_price'), output_field=DecimalField())
    ).aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0

    today_orders_count = outgoing_docs_today.count()
    today_products_sold_count = sales_items_today.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    today_new_customers = "N/A" # Заглушка
    today_profit = sales_items_today.annotate(
        profit=ExpressionWrapper((F('product__selling_price') - F('product__purchase_price')) * F('quantity'), output_field=DecimalField())
    ).aggregate(total_profit=Sum('profit'))['total_profit'] or 0

    low_stock_products = Stock.objects.filter(quantity__lte=F('product__minimum_stock_level')).select_related('product', 'warehouse')
    recent_documents = Document.objects.order_by('-document_date')[:7]

    context = {
        'today_revenue': today_revenue,
        'today_orders_count': today_orders_count,
        'today_products_sold_count': today_products_sold_count,
        'today_new_customers': today_new_customers,
        'today_profit': today_profit,
        'low_stock_products': low_stock_products,
        'recent_documents': recent_documents,
        'page_title': "Dashboard Overview"
    }

    return render(request, 'dashboard/dashboard.html', context)

@login_required
@manager_required
def revenue_chart_data(request):
    """Предоставляет данные для графика выручки."""
    today = date.today()
    start_date = today - timedelta(days=6)
    
    revenue_by_day = { (start_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(7) }

    sales_data = OutgoingItem.objects.filter(
        outgoing_transaction__document__document_date__date__gte=start_date
    ).annotate(
        sale_date=F('outgoing_transaction__document__document_date__date'),
        revenue=ExpressionWrapper(F('quantity') * F('product__selling_price'), output_field=DecimalField())
    ).values('sale_date').annotate(daily_revenue=Sum('revenue')).order_by('sale_date')

    for entry in sales_data:
        day_str = entry['sale_date'].strftime('%Y-%m-%d')
        if day_str in revenue_by_day:
            revenue_by_day[day_str] = entry['daily_revenue']
            
    labels = list(revenue_by_day.keys())
    data = list(revenue_by_day.values())

    return JsonResponse({
        'labels': labels,
        'data': data,
    })
