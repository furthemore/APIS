from __future__ import unicode_literals
import json
from django.db import models
from django.utils import timezone


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
    registeredDate = models.DateTimeField(auto_now_add=True, null=True)

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
    codeName = models.CharField(max_length=100)
    percentOff = models.IntegerField(null=True)
    amountOff = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
      return self.codeName

    def isValid(self):
        now = timezone.now()
        if self.startDate > now or self.endDate < now:
            return False
        return True

#TODO: fix
class Order(models.Model):
    total = models.DecimalField(max_digits=6, decimal_places=2)
    reference = models.CharField(max_length=50)
    createdDate = models.DateTimeField(auto_now_add=True, null=True)
    settledDate = models.DateTimeField(auto_now_add=True, null=True)
    discount = models.ForeignKey(Discount, null=True, on_delete=models.SET_NULL)
    orgDonation = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    charityDonation = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    notes = models.TextField(blank=True)
    billingName = models.CharField(max_length=200)
    billingAddress1 = models.CharField(max_length=200)
    billingAddress2 = models.CharField(max_length=200, blank=True)
    billingCity = models.CharField(max_length=200)
    billingState = models.CharField(max_length=200)
    billingCountry = models.CharField(max_length=200)
    billingPostal = models.CharField(max_length=20)
    billingEmail = models.CharField(max_length=200)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True)
    attendee = models.ForeignKey(Attendee)
    priceLevel = models.ForeignKey(PriceLevel)
    confirmationCode = models.CharField(max_length=100)
    enteredBy = models.CharField(max_length=100)
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)

class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption)
    orderItem = models.ForeignKey(OrderItem)
    optionValue = models.CharField(max_length=200)

 
