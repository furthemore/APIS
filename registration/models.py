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

class TableSize(LookupTable):
    description = models.TextField()
    chairMin = models.IntegerField(default=1)
    chairMax = models.IntegerField(default=1)
    tableMin = models.IntegerField(default=0)
    tableMax = models.IntegerField(default=0)
    partnerMin = models.IntegerField(default=1)
    partnerMax = models.IntegerField(default=1)
    basePrice = models.DecimalField(max_digits=6, decimal_places=2, default=0)

class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

    def __str__(self):
      return self.name

#End lookup and supporting tables

#Start CustomAddons
class Jersey(models.Model):
    shirtSize = models.ForeignKey(ShirtSizes)
    name = models.CharField(max_length=50)
    number = models.IntegerField()

#End CustomAddons

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

    def __str__(self):
      return '%s %s' % (self.firstName, self.lastName)

    def toJson(self):
      pass


class Staff(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    registrationToken = models.CharField(max_length=200)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    supervisor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, blank=True)
    twitter = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)
    attendee = models.ForeignKey(ShirtSizes, null=True, blank=True, on_delete=models.SET_NULL)    
    timesheetAccess = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    specialSkills = models.TextField(blank=True)
    specialFood = models.TextField(blank=True)
    specialMedical = models.TextField(blank=True)
    contactName = models.CharField(max_length=200, blank=True)
    contactPhone = models.CharField(max_length=200, blank=True)
    needRoom = models.BooleanField(default=False)
    gender = models.CharField(max_length=50, blank=True)     

class Dealer(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    registrationToken = models.CharField(max_length=200)
    approved = models.BooleanField(default=False)
    tableNumber = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    businessName = models.CharField(max_length=200)
    website = models.CharField(max_length=500)
    description = models.TextField()
    license = models.CharField(max_length=50)
    needPower = models.BooleanField(default=False)
    needWifi = models.BooleanField(default=False)
    wallSpace = models.BooleanField(default=False)
    nearTo = models.CharField(max_length=200, blank=True)
    farFrom = models.CharField(max_length=200, blank=True)
    tableSize = models.ForeignKey(TableSize)
    chairs = models.IntegerField(default=0)
    tables = models.IntegerField(default=0)
    reception = models.BooleanField(default=False)
    artShow = models.BooleanField(default=False)
    charityRaffle = models.TextField(blank=True)
    agreeToRules = models.BooleanField(default=False)
    breakfast = models.BooleanField(default=False)
    willSwitch = models.BooleanField(default=False)
    partners = models.TextField(blank=True)
    buttonOffer = models.CharField(max_length=200, blank=True)
    discount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    discountReason = models.CharField(max_length=200, blank=True)

    def __str__(self):
      return '%s %s' % (self.attendee.firstName, self.attendee.lastName)

    def toJson(self): 
      pass

    def paid(self):
      priceLevel = PriceLevel.objects.get(name='Dealer')
      orderItems = OrderItem.objects.filter(attendee=self.attendee, priceLevel=priceLevel)
      return orderItems.count() > 0


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
    required = models.BooleanField(default=False)

    def __str__(self):
      return '%s - %s' % (self.priceLevel, self.optionName)

    def getList(self):
	if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{'name':s.name, 'id':s.id} for s in ShirtSizes.objects.all()]
        else:
            return []

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

class Order(models.Model):
    total = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')
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

 
