
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import (
    Product, Warehouse, Document, Stock, Role, Supplier, Client, ProductCategory,
    LogIncoming, LogOutgoing, LogStock
)

# Используем кастомную модель пользователя
User = get_user_model()

class InventoryTests(TestCase):
    """
    Комплексный набор тестов для приложения inventory.
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
        cls.supplier = Supplier.objects.create(company_name='Надёжный Поставщик')
        cls.client_obj = Client.objects.create(company_name='Главный Клиент')
        cls.category = ProductCategory.objects.create(category_name='Ноутбуки')

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
            serial_number='AIR13-SN456'
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
        urls_to_check = [
            reverse('stock_list'),
            reverse('document_list'),
            reverse('incoming_transaction'),
            reverse('outgoing_transaction'),
        ]
        for url in urls_to_check:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_incoming_transaction_logic_and_logging(self):
        """Тест: создание документа прихода увеличивает остатки и создает логи."""
        self.assertFalse(Stock.objects.filter(product=self.product2).exists())

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

        response = self.client.post(reverse('incoming_transaction'), data=form_data)
        self.assertRedirects(response, reverse('document_list'))

        # Проверка обновления остатков
        stock1 = Stock.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(stock1.quantity, 15)
        stock2 = Stock.objects.get(product=self.product2, warehouse=self.warehouse)
        self.assertEqual(stock2.quantity, 20)

        # Проверка создания документа
        doc = Document.objects.get(document_type='Приход')
        self.assertEqual(doc.staff, self.user)
        self.assertEqual(doc.incomingtransaction.items.count(), 2)

        # Проверка создания логов
        self.assertEqual(LogIncoming.objects.count(), 1)
        log_incoming = LogIncoming.objects.first()
        self.assertEqual(log_incoming.incoming_transaction, doc.incomingtransaction)
        self.assertEqual(log_incoming.user_add, self.user)

        self.assertEqual(LogStock.objects.filter(operation_type='Приход').count(), 2)
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
            'items-0-quantity': initial_stock_quantity + 1,
        }

        response = self.client.post(reverse('outgoing_transaction'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Недостаточно товара')

        # Убеждаемся, что остаток и логи не изменились
        self.assertEqual(Stock.objects.get(product=self.product1).quantity, initial_stock_quantity)
        self.assertFalse(Document.objects.filter(document_type='Расход').exists())
        self.assertFalse(LogOutgoing.objects.exists())
        self.assertFalse(LogStock.objects.filter(operation_type='Расход').exists())

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

        response = self.client.post(reverse('outgoing_transaction'), data=form_data)
        self.assertRedirects(response, reverse('document_list'))

        # Проверка обновления остатков
        final_stock = Stock.objects.get(product=self.product1)
        self.assertEqual(final_stock.quantity, initial_stock_quantity - quantity_to_ship)

        # Проверка создания документа
        doc = Document.objects.get(document_type='Расход')
        self.assertEqual(doc.outgoingtransaction.items.count(), 1)

        # Проверка создания логов
        self.assertEqual(LogOutgoing.objects.count(), 1)
        log_outgoing = LogOutgoing.objects.first()
        self.assertEqual(log_outgoing.outgoing_transaction, doc.outgoingtransaction)
        self.assertEqual(log_outgoing.user_add, self.user)

        self.assertEqual(LogStock.objects.filter(operation_type='Расход').count(), 1)
        log_stock = LogStock.objects.get(operation_type='Расход')
        self.assertEqual(log_stock.stock, final_stock)
        self.assertEqual(log_stock.details, f'Расход товара: {quantity_to_ship} шт.')
