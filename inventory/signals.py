# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.db import transaction
# from .models import IncomingItem, OutgoingItem, Stock, LogIncoming, LogOutgoing, LogStock
# import logging

# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=IncomingItem)
# def handle_incoming_item(sender, instance, created, **kwargs):
#     if created:
#         with transaction.atomic():
#             stock, created = Stock.objects.get_or_create(
#                 product=instance.product,
#                 warehouse=instance.incoming_transaction.warehouse,
#                 defaults={'quantity': 0}
#             )
#             stock.quantity += instance.quantity
#             stock.save()

#             LogStock.objects.create(
#                 stock=stock,
#                 operation_type="Приход",
#                 user_add=instance.incoming_transaction.document.staff,
#                 details=f"Приход товара: {instance.quantity} шт."
#             )

#             LogIncoming.objects.create(
#                 incoming_transaction=instance.incoming_transaction,
#                 operation_type="CREATE",
#                 user_add=instance.incoming_transaction.document.staff
#             )

# @receiver(post_save, sender=OutgoingItem)
# def handle_outgoing_item(sender, instance, created, **kwargs):
#     if created:
#         try:
#             with transaction.atomic():
#                 stock = Stock.objects.select_for_update().get(
#                     product=instance.product,
#                     warehouse=instance.outgoing_transaction.warehouse
#                 )

#                 if stock.quantity >= instance.quantity:
#                     stock.quantity -= instance.quantity
#                     stock.save()

#                     LogStock.objects.create(
#                         stock=stock,
#                         operation_type="Расход",
#                         user_add=instance.outgoing_transaction.document.staff,
#                         details=f"Расход товара: {instance.quantity} шт."
#                     )
#                 else:
#                     logger.warning(
#                         f"Недостаточно товара на складе для списания (Товар: {instance.product.sku}, Склад: {instance.outgoing_transaction.warehouse.name}). "
#                         f"Требуется: {instance.quantity}, в наличии: {stock.quantity}. Остаток не был изменен."
#                     )

#         except Stock.DoesNotExist:
#             logger.error(
#                 f"Попытка списания несуществующего на складе товара (Товар: {instance.product.sku}, Склад: {instance.outgoing_transaction.warehouse.name}). "
#                 f"Остаток не был изменен."
#             )
        
#         # Этот лог должен создаваться всегда, т.к. документ расхода был создан
#         LogOutgoing.objects.create(
#             outgoing_transaction=instance.outgoing_transaction,
#             operation_type="CREATE",
#             user_add=instance.outgoing_transaction.document.staff
#         )
