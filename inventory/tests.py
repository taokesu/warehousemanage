from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import (
    Product, Warehouse, Document, Stock, Role, Supplier, Client, ProductCategory,
    LogIncoming, LogOutgoing, LogStock
)

# Используем кастомную модель пользователя
User = get_user_model()

class InventoryIntegrationTests(TestCase):
    """
    Комплексный набор ИНТЕГРАЦИОННЫХ тестов для приложения inventory.
    Они проверяют всю систему в сборе: от HTTP-запроса до ответа.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Настройка данных, которые будут использоваться во всех тестах этого класса.
        Этот метод выполняется один раз.
        """
        # Создаем базовые сущности
        cls.role = Role.objects.create(role_name='Кладовщик')
        cls.user = User.objects.create_user(
            username='testuser', 
            password='password123',
            first_name='Иван',
            last_name='Петров',
            role=cls.role
        )
        cls.warehouse = Warehouse.objects.create(name='Основной склад')
        cls.supplier = Supplier.objects.create(company_name='Надёжный Поставщик') # ИСПРАВЛЕНО
        cls.client_obj = Client.objects.create(company_name='Главный Клиент') # ИСПРАВЛЕНО
        cls.category = ProductCategory.objects.create(category_name='Ноутбуки') # ИСПРАВЛЕНО

        # Создаем товары
        cls.product1 = Product.objects.create(
            category=cls.category, 
            product_name='Ноутбук Pro 15', 
            purchase_price=90000.00, 
            selling_price=120000.00, 
            serial_number='PRO15-SN123'
        )
        cls.product2 = Product.objects.create(
            category=cls.category, 
            product_name='Ноутбук Air 13', 
            purchase_price=70000.00, 
            selling_price=95000.00,
        )

        # Создаем начальный остаток для тестов расхода
        Stock.objects.create(warehouse=cls.warehouse, product=cls.product1, quantity=10)

    def setUp(self):
        """
        Этот метод выполняется перед каждым тестом.
        """
        # Выполняем вход пользователя в систему
        self.client.login(username='testuser', password='password123')

    def test_view_access_unauthenticated(self):
        """Проверка: неавторизованный пользователь перенаправляется на страницу входа."""
        self.client.logout()
        # Этот список можно расширить
        urls_to_check = [
            reverse('stock_list'),
            reverse('document_list'),
        ]
        for url in urls_to_check:
            response = self.client.get(url)
            self.assertRedirects(response, f'/login/?next={url}')

    def test_incoming_transaction_logic_and_logging(self):
        """Тест: создание документа прихода увеличивает остатки и создает логи."""
        # До теста товара product2 на складе нет
        self.assertFalse(Stock.objects.filter(product=self.product2).exists())

        # Данные формы для создания приходной накладной
        form_data = {
            'supplier': self.supplier.id,
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '2',
            'items-INITIAL_FORMS': '0',
            'items-0-product': self.product1.id,
            'items-0-quantity': '5',
            'items-1-product': self.product2.id,
            'items-1-quantity': '20',
        }
        
        # Отправляем POST-запрос, имитируя пользователя
        response = self.client.post(reverse('incoming_transaction'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200) # Успешный редирект и загрузка страницы

        # Проверка обновления остатков
        stock1 = Stock.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(stock1.quantity, 15) # Было 10, стало 15
        stock2 = Stock.objects.get(product=self.product2, warehouse=self.warehouse)
        self.assertEqual(stock2.quantity, 20) # Было 0, стало 20

        # Проверка создания логов
        self.assertTrue(LogStock.objects.filter(stock=stock1, operation_type='Приход', details='Приход товара: 5 шт.').exists())
        self.assertTrue(LogStock.objects.filter(stock=stock2, operation_type='Приход', details='Приход товара: 20 шт.').exists())

    def test_outgoing_transaction_insufficient_stock(self):
        """Тест: система блокирует отгрузку при нехватке товара."""
        initial_stock_quantity = Stock.objects.get(product=self.product1).quantity

        form_data = {
            'client': self.client_obj.id,
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-product': self.product1.id,
            'items-0-quantity': initial_stock_quantity + 1, # Пытаемся отгрузить больше, чем есть
        }

        response = self.client.post(reverse('outgoing_transaction'), data=form_data)
        self.assertEqual(response.status_code, 200) # Страница перезагружается с ошибкой
        self.assertContains(response, 'Недостаточно товара') # Проверяем текст ошибки на странице

        # Убеждаемся, что остаток не изменился
        self.assertEqual(Stock.objects.get(product=self.product1).quantity, initial_stock_quantity)
        
    def test_successful_outgoing_transaction_and_logging(self):
        """Тест: успешная отгрузка товара уменьшает остатки и создает логи."""
        initial_stock_quantity = Stock.objects.get(product=self.product1).quantity
        quantity_to_ship = 7

        form_data = {
            'client': self.client_obj.id,
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-product': self.product1.id,
            'items-0-quantity': quantity_to_ship,
        }

        response = self.client.post(reverse('outgoing_transaction'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверка обновления остатков
        final_stock = Stock.objects.get(product=self.product1)
        self.assertEqual(final_stock.quantity, initial_stock_quantity - quantity_to_ship)

        # Проверка создания логов
        self.assertTrue(LogStock.objects.filter(stock=final_stock, operation_type='Расход', details=f'Расход товара: {quantity_to_ship} шт.').exists())


class ModelUnitTests(TestCase):
    """
    Набор "чистых" МОДУЛЬНЫХ тестов (unit-tests), которые проверяют
    логику моделей в изоляции, без использования HTTP-клиента и БД (где возможно).
    """

    def test_product_str_representation(self):
        """Тест: __str__ модели Product с серийным номером и без него."""
        # 1. Продукт БЕЗ серийного номера
        product_no_sn = Product(product_name="Тестовый продукт 123")
        self.assertEqual(str(product_no_sn), "Тестовый продукт 123 (б/н)")

        # 2. Продукт С серийным номером
        product_with_sn = Product(product_name="Другой продукт", serial_number="SN-XYZ-789")
        self.assertEqual(str(product_with_sn), "Другой продукт (SN-XYZ-789)")

    def test_warehouse_str_representation(self):
        """Тест: __str__ модели Warehouse возвращает ее имя."""
        warehouse = Warehouse(name="Склад для юнит-теста")
        self.assertEqual(str(warehouse), "Склад для юнит-теста")

    def test_stock_str_representation(self):
        """Тест: __str__ модели Stock показывает товар, склад и количество."""
        product = Product(product_name="Тестовый Болт")
        warehouse = Warehouse(name="Склад А")
        stock = Stock(product=product, warehouse=warehouse, quantity=150)
        
        expected_str = "Тестовый Болт на складе Склад А: 150 шт."
        self.assertEqual(str(stock), expected_str)
        
    def test_document_str_representation(self):
        """Тест: __str__ модели Document показывает его тип и номер."""
        # ИСПРАВЛЕНО: Создаем полные объекты, необходимые для str
        role = Role.objects.create(role_name='Тестовая роль')
        user = User.objects.create_user(username='str_test_user', role=role)
        doc = Document.objects.create(staff=user, document_type=Document.DocumentType.INCOMING)
        
        expected_str = f"Документ №{doc.id} (Приход) от {doc.document_date.strftime('%Y-%m-%d')}"
        self.assertEqual(str(doc), expected_str)

