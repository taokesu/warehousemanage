from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Role, Staff, Warehouse, Supplier, Client, ProductCategory, Product, 
    Stock, Document, IncomingTransaction, OutgoingTransaction, 
    IncomingItem, OutgoingItem, LogIncoming, LogOutgoing, LogStock
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    search_fields = ('role_name',)

class StaffAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('patronymic', 'role')}),
    )
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(Staff, StaffAdmin)

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity')
    search_fields = ('name', 'address')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'phone')
    search_fields = ('company_name', 'contact_person')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'phone')
    search_fields = ('company_name', 'contact_person')

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'serial_number', 'purchase_price', 'minimum_stock_level')
    list_editable = ('minimum_stock_level',)
    list_filter = ('category',)
    search_fields = ('product_name', 'serial_number')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity')
    list_filter = ('warehouse',)
    search_fields = ('product__product_name', 'warehouse__name')
    readonly_fields = ('quantity',)

class IncomingItemInline(admin.TabularInline):
    model = IncomingItem
    extra = 1

@admin.register(IncomingTransaction)
class IncomingTransactionAdmin(admin.ModelAdmin):
    list_display = ('document', 'supplier', 'warehouse', 'total_amount')
    inlines = [IncomingItemInline]
    readonly_fields = ('total_amount',)

class OutgoingItemInline(admin.TabularInline):
    model = OutgoingItem
    extra = 1

@admin.register(OutgoingTransaction)
class OutgoingTransactionAdmin(admin.ModelAdmin):
    list_display = ('document', 'client', 'warehouse', 'total_amount')
    inlines = [OutgoingItemInline]
    readonly_fields = ('total_amount',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_type', 'document_date', 'staff')
    list_filter = ('document_type', 'staff')

# --- Log Models Admin ---

@admin.register(LogIncoming)
class LogIncomingAdmin(admin.ModelAdmin):
    list_display = ('incoming_transaction', 'operation_type', 'user_add', 'datetime_add')
    list_filter = ('operation_type', 'user_add', 'datetime_add')
    search_fields = ('incoming_transaction__id',)
    readonly_fields = ('incoming_transaction', 'operation_type', 'user_add', 'datetime_add')

@admin.register(LogOutgoing)
class LogOutgoingAdmin(admin.ModelAdmin):
    list_display = ('outgoing_transaction', 'operation_type', 'user_add', 'datetime_add')
    list_filter = ('operation_type', 'user_add', 'datetime_add')
    search_fields = ('outgoing_transaction__id',)
    readonly_fields = ('outgoing_transaction', 'operation_type', 'user_add', 'datetime_add')

@admin.register(LogStock)
class LogStockAdmin(admin.ModelAdmin):
    list_display = ('stock', 'operation_type', 'user_add', 'datetime_add')
    list_filter = ('operation_type', 'user_add', 'datetime_add')
    search_fields = ('stock__product__product_name',)
    readonly_fields = ('stock', 'operation_type', 'user_add', 'datetime_add', 'details')
