
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

# Импортируем модели из inventory, так как отчеты строятся на этих данных
from inventory.models import (
    Product, Warehouse, Stock, Role, ProductCategory
)

User = get_user_model()

class ReportsTests(TestCase):
    """
    Набор тестов для приложения reports.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Подготовка данных, которые будут использоваться во всех тестах отчетов.
        """
        # Создаем пользователя с ролью Менеджер, так как отчеты для него
        cls.role = Role.objects.create(role_name='Менеджер')
        cls.user = User.objects.create_user(
            username='testmanager',
            password='password123',
            role=cls.role
        )
        
        # Создаем склад и категорию
        cls.warehouse = Warehouse.objects.create(name='Основной склад')
        cls.category = ProductCategory.objects.create(category_name='Тестовая категория')

        # Создаем несколько товаров
        cls.product1 = Product.objects.create(
            category=cls.category,
            product_name='Тестовый товар 1',
            purchase_price=100.00,
            selling_price=150.00
        )
        cls.product2 = Product.objects.create(
            category=cls.category,
            product_name='Тестовый товар 2 (Нулевой остаток)',
            purchase_price=200.00,
            selling_price=250.00
        )

        # Создаем остатки на складе для этих товаров
        Stock.objects.create(warehouse=cls.warehouse, product=cls.product1, quantity=25)
        Stock.objects.create(warehouse=cls.warehouse, product=cls.product2, quantity=0)

    def setUp(self):
        """
        Выполняем вход пользователя перед каждым тестом.
        """
        self.client.login(username='testmanager', password='password123')

    def test_report_list_view_authenticated(self):
        """
        Тест: страница со списком отчетов доступна менеджеру и содержит ссылки.
        """
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/report_list.html')
        # Проверяем наличие названий отчетов на странице
        self.assertContains(response, 'Отчет по остаткам товаров')
        self.assertContains(response, 'Отчет по движению товаров')

    def test_report_list_view_unauthenticated(self):
        """
        Тест: неавторизованный пользователь перенаправляется на страницу входа.
        """
        self.client.logout()
        response = self.client.get(reverse('report_list'))
        # Проверяем редирект на страницу логина
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('report_list')}")

    def test_stock_report_view(self):
        """
        Тест: отчет по остаткам товаров корректно формируется и отображает данные.
        """
        response = self.client.get(reverse('stock_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/stock_report.html')

        # Проверяем, что в контексте страницы есть нужные данные
        self.assertIn('stocks', response.context)
        stocks_in_context = response.context['stocks']
        self.assertEqual(stocks_in_context.count(), 2)

        # Проверяем, что на отрендеренной странице есть данные наших товаров
        self.assertContains(response, 'Тестовый товар 1')
        self.assertContains(response, '25')  # Остаток первого товара
        self.assertContains(response, 'Тестовый товар 2 (Нулевой остаток)')
        self.assertContains(response, '0')   # Остаток второго товара
