from __future__ import unicode_literals
import json
from django.db import models
from django.utils import timezone

from payments.models import BasePayment

#######################################
# As of Data Model version 27
#######################################


# Lookup and supporting tables.
class LookupTable(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
      return self.name

    class Meta: 
        abstract = True

class HoldType(LookupTable):
    pass

class ShirtSizes(LookupTable):
    pass

class Event(LookupTable):
    pass

class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

    def __str__(self):
      return self.name

#End lookup and supporting tables



class Attendee(models.Model):
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    postalCode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=200)
    birthdate = models.DateField()
    badgeName = models.CharField(max_length=200, blank=True)
    badgeNumber = models.IntegerField(null=True, blank=True)
    badgePrinted = models.BooleanField(default=False)
    emailsOk = models.BooleanField(default=False)
    volunteerContact = models.BooleanField(default=False)
    volunteerDepts = models.CharField(max_length=1000, blank=True)
    holdType = models.ForeignKey(HoldType, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    parentFirstName = models.CharField(max_length=200, blank=True)
    parentLastName = models.CharField(max_length=200, blank=True)
    parentPhone = models.CharField(max_length=20, blank=True)
    parentEmail = models.CharField(max_length=200, blank=True)
    event = models.ForeignKey(Event)    


class Dealer(models.Model):
    pass


class Staff(models.Model):
    pass




# Start order tables
class PriceLevel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    basePrice = models.DecimalField(max_digits=6, decimal_places=2)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    public = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
      return self.name

class PriceLevelOption(models.Model):
    priceLevel = models.ForeignKey(PriceLevel)
    optionName = models.CharField(max_length=200)
    optionPrice = models.DecimalField(max_digits=6, decimal_places=2)
    optionExtraType = models.CharField(max_length=100, blank=True)

    def __str__(self):
      return '%s - %s' % (self.priceLevel, self.optionName)

class Discount(models.Model):
    requiredPriceLevel = models.ForeignKey(PriceLevel, null=True, on_delete=models.SET_NULL)
    codeName = models.CharField(max_length=100)
    percentOff = models.IntegerField(null=True)
    amountOff = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
      return self.codeName

    def isValid(self, requiredPriceId=None):
        now = timezone.now()
        if self.startDate > now or self.endDate < now:
            return False
        if requiredPriceId is not None and self.requiredPriceLevel is not None and self.requiredPriceLevel.id != requiredPriceId:
            return False
        return True

class Order(BasePayment):
    discount = models.ForeignKey(Discount, null=True, on_delete=models.SET_NULL)
    orgDonation = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    charityDonation = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    def get_failure_url(self):
      return 'http://dawningbrooke.net/registration/failure/'

    def get_success_url(self):
      return 'http://dawningbrooke.net/registration/success/'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True)
    attendee = models.ForeignKey(Attendee)
    priceLevel = models.ForeignKey(PriceLevel)
    confirmationCode = models.CharField(max_length=100)
    enteredBy = models.CharField(max_length=100)

class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption)
    orderItem = models.ForeignKey(OrderItem)
    optionValue = models.CharField(max_length=200)

 
