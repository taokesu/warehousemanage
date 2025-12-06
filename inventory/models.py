from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, unique=True)
    minimum_stock_level = models.IntegerField(default=10)

    def __str__(self):
        return self.product_name

class Document(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('Приход', 'Приход'),
        ('Расход', 'Расход'),
    ]
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES)
    date = models.DateField()

    def __str__(self):
        return f"{self.document_type} №{self.id} от {self.date}"

class Transaction(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='transactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} шт."

    @property
    def total_cost(self):
        return self.quantity * self.price

class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('product', 'warehouse')

    def __str__(self):
        return f"{self.product.product_name} на складе {self.warehouse.name}: {self.quantity} шт."
