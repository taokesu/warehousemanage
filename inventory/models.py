from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

class Staff(AbstractUser):
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Роль")

    def get_full_name_initials(self):
        """
        Возвращает полное имя в формате 'Фамилия И. О.'.
        """
        if self.last_name:
            name_str = f"{self.last_name}"
            if self.first_name:
                name_str += f" {self.first_name[0]}."
            if self.patronymic:
                name_str += f" {self.patronymic[0]}."
            return name_str
        return self.username

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class Warehouse(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название склада")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адрес")
    capacity = models.IntegerField(blank=True, null=True, verbose_name="Вместимость")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"

class Supplier(models.Model):
    company_name = models.CharField(max_length=255, verbose_name="Название компании")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Контактное лицо")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Телефон")

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"


class Client(models.Model):
    company_name = models.CharField(max_length=255, verbose_name="Название компании")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Контактное лицо")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Телефон")

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

class ProductCategory(models.Model):
    category_name = models.CharField(max_length=100, verbose_name="Название категории")

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товаров"

class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.RESTRICT, verbose_name="Категория")
    product_name = models.CharField(max_length=255, verbose_name="Название товара")
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Серийный номер")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Закупочная цена")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена продажи", default=0)
    minimum_stock_level = models.IntegerField(verbose_name="Минимальный остаток", default=10, null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.serial_number or 'б/н' })"

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.RESTRICT, verbose_name="Склад")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    def __str__(self):
        return f"{self.product.product_name} на складе {self.warehouse.name}: {self.quantity} шт."

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name = "Остаток на складе"
        verbose_name_plural = "Остатки на складе"

class Document(models.Model):
    class DocumentType(models.TextChoices):
        INCOMING = 'Приход', _('Приход')
        OUTGOING = 'Расход', _('Расход')

    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT, verbose_name="Сотрудник")
    document_type = models.CharField(max_length=50, choices=DocumentType.choices, verbose_name="Тип документа")
    document_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата документа")

    def __str__(self):
        return f"Документ №{self.id} ({self.get_document_type_display()}) от {self.document_date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

class IncomingTransaction(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, primary_key=True, verbose_name="Документ")
    supplier = models.ForeignKey(Supplier, on_delete=models.RESTRICT, verbose_name="Поставщик")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.RESTRICT, verbose_name="Склад", default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма", default=0)

    def __str__(self):
        return f"Приход №{self.document.id} от {self.supplier.company_name}"
    
    class Meta:
        verbose_name = "Операция прихода"
        verbose_name_plural = "Операции прихода"


class OutgoingTransaction(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, primary_key=True, verbose_name="Документ")
    client = models.ForeignKey(Client, on_delete=models.RESTRICT, verbose_name="Клиент")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.RESTRICT, verbose_name="Склад", default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма", default=0)

    def __str__(self):
        return f"Расход №{self.document.id} для {self.client.company_name}"

    class Meta:
        verbose_name = "Операция расхода"
        verbose_name_plural = "Операции расхода"

class IncomingItem(models.Model):
    incoming_transaction = models.ForeignKey(IncomingTransaction, related_name='items', on_delete=models.CASCADE, verbose_name="Операция прихода")
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, verbose_name="Товар")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    @property
    def line_total_purchase(self):
        return self.quantity * self.product.purchase_price

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} шт."
    
    class Meta:
        verbose_name = "Позиция в приходе"
        verbose_name_plural = "Позиции в приходе"

class OutgoingItem(models.Model):
    outgoing_transaction = models.ForeignKey(OutgoingTransaction, related_name='items', on_delete=models.CASCADE, verbose_name="Операция расхода")
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, verbose_name="Товар")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    @property
    def line_total_selling(self):
        return self.quantity * self.product.selling_price

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} шт."

    class Meta:
        verbose_name = "Позиция в расходе"
        verbose_name_plural = "Позиции в расходе"

# --- Logging Models ---

class LogIncoming(models.Model):
    incoming_transaction = models.ForeignKey(IncomingTransaction, on_delete=models.CASCADE, verbose_name="Операция прихода")
    operation_type = models.CharField(max_length=10, verbose_name="Тип операции")
    user_add = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    datetime_add = models.DateTimeField(auto_now_add=True, verbose_name="Время операции")

    def __str__(self):
        return f"Log for Incoming Transaction {self.incoming_transaction_id} at {self.datetime_add}"

    class Meta:
        verbose_name = "Лог прихода"
        verbose_name_plural = "Логи прихода"

class LogOutgoing(models.Model):
    outgoing_transaction = models.ForeignKey(OutgoingTransaction, on_delete=models.CASCADE, verbose_name="Операция расхода")
    operation_type = models.CharField(max_length=10, verbose_name="Тип операции")
    user_add = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    datetime_add = models.DateTimeField(auto_now_add=True, verbose_name="Время операции")

    def __str__(self):
        return f"Log for Outgoing Transaction {self.outgoing_transaction_id} at {self.datetime_add}"

    class Meta:
        verbose_name = "Лог расхода"
        verbose_name_plural = "Логи расхода"

class LogStock(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, verbose_name="Остаток на складе")
    operation_type = models.CharField(max_length=10, verbose_name="Тип операции")
    user_add = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    datetime_add = models.DateTimeField(auto_now_add=True, verbose_name="Время операции")
    details = models.TextField(blank=True, null=True, verbose_name="Детали")

    def __str__(self):
        return f"Log for Stock {self.stock_id} - {self.operation_type} at {self.datetime_add}"

    class Meta:
        verbose_name = "Лог остатков"
        verbose_name_plural = "Логи остатков"