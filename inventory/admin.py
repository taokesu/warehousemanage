from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Role, Staff, Warehouse, Supplier, Customer, Product, 
    Document, Transaction
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
        ('Custom Fields', {'fields': ('role',)}),
    )
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(Staff, StaffAdmin)

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'serial_number', 'minimum_stock_level')
    list_editable = ('minimum_stock_level',)
    search_fields = ('product_name', 'serial_number')

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 1

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_type', 'date')
    list_filter = ('document_type',)
    inlines = [TransactionInline]
