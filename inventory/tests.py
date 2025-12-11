
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Warehouse, Document, DocumentItem, Stock

# Получаем активную модель пользователя
User = get_user_model()

class InventoryTestCase(TestCase):
    """
    Базовый класс для тестов с общими данными.
    """
    def setUp(self):
        # Создаем пользователя-сотрудника
        self.user = User.objects.create_user(
            username='testuser', 
            password='password123',
            first_name='Иван',
            last_name='Петров',
            role='Storekeeper'
        )
        # Аутентифицируем пользователя
        self.client.login(username='testuser', password='password123')

        # Создаем основные объекты
        self.warehouse = Warehouse.objects.create(name='Основной склад')
        self.product1 = Product.objects.create(name='Ноутбук', article='NB-001')
        self.product2 = Product.objects.create(name='Монитор', article='MN-002')

class ModelCreationTests(InventoryTestCase):
    """
    Тесты для проверки корректного создания моделей.
    """
    def test_product_creation(self):
        self.assertEqual(self.product1.name, 'Ноутбук')
        self.assertEqual(str(self.product1), 'Ноутбук (NB-001)')

    def test_warehouse_creation(self):
        self.assertEqual(self.warehouse.name, 'Основной склад')
        self.assertEqual(str(self.warehouse), 'Основной склад')

    def test_staff_creation(self):
        self.assertEqual(self.user.get_full_name(), 'Петров Иван')
        self.assertEqual(str(self.user), 'Петров И.')


class ViewAccessTests(InventoryTestCase):
    """
    Тесты для проверки доступа к представлениям (страницам).
    """
    def test_unauthenticated_access_redirect(self):
        # Выходим из системы
        self.client.logout()
        # Проверяем редирект на страницу входа
        response = self.client.get(reverse('stock_list'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("stock_list")}')
        
        response = self.client.get(reverse('document_list'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("document_list")}')

    def test_authenticated_access_success(self):
        # Проверяем, что авторизованный пользователь получает доступ
        response = self.client.get(reverse('stock_list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('document_list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('incoming_transaction'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('outgoing_transaction'))
        self.assertEqual(response.status_code, 200)


class TransactionLogicTests(InventoryTestCase):
    """
    Тесты для проверки бизнес-логики создания документов прихода и расхода.
    """
    def test_incoming_transaction_creates_stock(self):
        """
        Проверка, что документ прихода корректно увеличивает остатки на складе.
        """
        self.assertEqual(Stock.objects.count(), 0)

        form_data = {
            'document_date': '2025-12-10 12:00:00',
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '2',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-product': self.product1.id,
            'items-0-quantity': '10',
            'items-1-product': self.product2.id,
            'items-1-quantity': '20',
        }

        response = self.client.post(reverse('incoming_transaction'), data=form_data)
        
        # Проверяем, что нас перенаправило на страницу списка документов
        self.assertRedirects(response, reverse('document_list'))
        
        # Проверяем, что был создан один документ
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.document_type, 'INCOMING')
        self.assertEqual(doc.items.count(), 2)

        # Проверяем, что остатки на складе корректно обновились
        self.assertEqual(Stock.objects.count(), 2)
        stock1 = Stock.objects.get(warehouse=self.warehouse, product=self.product1)
        self.assertEqual(stock1.quantity, 10)

        stock2 = Stock.objects.get(warehouse=self.warehouse, product=self.product2)
        self.assertEqual(stock2.quantity, 20)

    def test_outgoing_transaction_with_insufficient_stock(self):
        """
        Проверка, что система не дает отгрузить товар, если его недостаточно на складе.
        """
        # Сначала создаем начальный остаток: 5 ноутбуков
        Stock.objects.create(warehouse=self.warehouse, product=self.product1, quantity=5)
        self.assertEqual(Stock.objects.get(product=self.product1).quantity, 5)

        # Пытаемся отгрузить 7 ноутбуков
        form_data = {
            'document_date': '2025-12-11 14:00:00',
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-product': self.product1.id,
            'items-0-quantity': '7',
        }

        response = self.client.post(reverse('outgoing_transaction'), data=form_data)
        
        # Проверяем, что страница не была перенаправлена, а показана снова с ошибкой
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Недостаточно товара на складе')

        # Проверяем, что новый документ НЕ был создан
        self.assertEqual(Document.objects.filter(document_type='OUTGOING').count(), 0)
        
        # Проверяем, что остаток на складе НЕ изменился
        self.assertEqual(Stock.objects.get(product=self.product1).quantity, 5)

    def test_successful_outgoing_transaction(self):
        """
        Проверка корректной отгрузки товара при достаточном остатке.
        """
        # Начальный остаток: 15 ноутбуков
        Stock.objects.create(warehouse=self.warehouse, product=self.product1, quantity=15)
        
        # Отгружаем 10 ноутбуков
        form_data = {
            'document_date': '2025-12-12 10:00:00',
            'warehouse': self.warehouse.id,
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-product': self.product1.id,
            'items-0-quantity': '10',
        }

        response = self.client.post(reverse('outgoing_transaction'), data=form_data)
        
        # Проверяем перенаправление
        self.assertRedirects(response, reverse('document_list'))

        # Проверяем, что документ расхода создан
        self.assertEqual(Document.objects.filter(document_type='OUTGOING').count(), 1)
        
        # Проверяем, что остаток на складе уменьшился
        final_stock = Stock.objects.get(warehouse=self.warehouse, product=self.product1)
        self.assertEqual(final_stock.quantity, 5)
