from django.db.models.signals import pre_save
from django.dispatch import receiver

from registration.models import Order


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance):
    if instance.billingState == None:
        instance.billingState = ""
