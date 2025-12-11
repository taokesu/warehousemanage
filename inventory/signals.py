from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import (
    IncomingTransaction, OutgoingTransaction, IncomingItem, OutgoingItem, 
    Stock, LogIncoming, LogOutgoing, LogStock
)

# --- Сигналы для логирования самих транзакций ---

@receiver(post_save, sender=IncomingTransaction)
def log_incoming_transaction(sender, instance, created, **kwargs):
    """Создает одну запись в логе при создании новой транзакции прихода."""
    if created:
        LogIncoming.objects.create(
            incoming_transaction=instance,
            operation_type="CREATE",
            user_add=instance.document.staff
        )

@receiver(post_save, sender=OutgoingTransaction)
def log_outgoing_transaction(sender, instance, created, **kwargs):
    """Создает одну запись в логе при создании новой транзакции расхода."""
    if created:
        LogOutgoing.objects.create(
            outgoing_transaction=instance,
            operation_type="CREATE",
            user_add=instance.document.staff
        )


# --- Сигналы для изменения остатков и их логирования --- 

@receiver(post_save, sender=IncomingItem)
def handle_incoming_item_stock(sender, instance, created, **kwargs):
    """При добавлении товара в приход, увеличивает остаток на складе и логирует это."""
    if created:
        with transaction.atomic():
            stock, _ = Stock.objects.get_or_create(
                product=instance.product,
                warehouse=instance.incoming_transaction.warehouse,
                defaults={'quantity': 0}
            )
            stock.quantity += instance.quantity
            stock.save()

            LogStock.objects.create(
                stock=stock,
                operation_type="Приход",
                user_add=instance.incoming_transaction.document.staff,
                details=f"Приход товара: {instance.quantity} шт."
            )

@receiver(post_save, sender=OutgoingItem)
def handle_outgoing_item_stock(sender, instance, created, **kwargs):
    """При добавлении товара в расход, уменьшает остаток на складе и логирует это."""
    if created:
        # Логика списания остатков перенесена во views.py для немедленной валидации.
        # Сигнал теперь только логирует изменение, которое уже было произведено.
        # В данном проекте основная логика списания происходит во views.py
        # в `outgoing_transaction_view` внутри `transaction.atomic()`.
        # Однако, если бы логика была только в сигналах, она была бы здесь.
        # Оставляем этот сигнал для консистентности и возможного будущего расширения.
        
        # Найдем остаток, который уже должен был быть изменен во view
        try:
            stock = Stock.objects.get(
                product=instance.product,
                warehouse=instance.outgoing_transaction.warehouse
            )
            LogStock.objects.create(
                stock=stock,
                operation_type="Расход",
                user_add=instance.outgoing_transaction.document.staff,
                details=f"Расход товара: {instance.quantity} шт."
            )
        except Stock.DoesNotExist:
            # Эта ситуация не должна произойти, если валидация во view работает правильно
            pass 
