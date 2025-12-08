from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Role, Staff, Warehouse, Supplier, Client, ProductCategory, Product, 
    Stock, Document, IncomingItem, OutgoingItem
    # LogIncoming, LogOutgoing, LogStock # Этих моделей нет в старой версии
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

# @admin.register(IncomingTransaction) # Этой модели нет, используем Document
# class IncomingTransactionAdmin(admin.ModelAdmin):
#     list_display = ('document', 'supplier', 'warehouse', 'total_amount')
#     inlines = [IncomingItemInline]
#     readonly_fields = ('total_amount',)

class OutgoingItemInline(admin.TabularInline):
    model = OutgoingItem
    extra = 1

# @admin.register(OutgoingTransaction) # Этой модели нет, используем Document
# class OutgoingTransactionAdmin(admin.ModelAdmin):
#     list_display = ('document', 'client', 'warehouse', 'total_amount')
#     inlines = [OutgoingItemInline]
#     readonly_fields = ('total_amount',)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_type', 'document_date', 'staff')
    list_filter = ('document_type', 'staff')

    def get_inlines(self, request, obj=None):
        if obj and obj.document_type == 'Приход':
            return [IncomingItemInline]
        elif obj and obj.document_type == 'Расход':
            return [OutgoingItemInline]
        return []

admin.site.register(Document, DocumentAdmin)
