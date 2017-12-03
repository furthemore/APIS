from __future__ import unicode_literals
import json
import random
import string
from decimal import *
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
    dealerRegStart = models.DateTimeField()
    dealerRegEnd = models.DateTimeField()
    staffRegStart = models.DateTimeField()
    staffRegEnd = models.DateTimeField()
    attendeeRegStart = models.DateTimeField()
    attendeeRegEnd = models.DateTimeField()
    onlineRegStart = models.DateTimeField()
    onlineRegEnd = models.DateTimeField()
    eventStart = models.DateField()
    eventEnd = models.DateField()

class TableSize(LookupTable):
    description = models.TextField()
    chairMin = models.IntegerField(default=1)
    chairMax = models.IntegerField(default=1)
    tableMin = models.IntegerField(default=0)
    tableMax = models.IntegerField(default=0)
    partnerMin = models.IntegerField(default=1)
    partnerMax = models.IntegerField(default=1)
    basePrice = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self): 
      if self.event is None:
        return self.name
      return self.name + " " + self.event.name

class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

    def __str__(self):
      return self.name

#End lookup and supporting tables


def getRegistrationToken():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(15))

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
    emailsOk = models.BooleanField(default=False)
    surveyOk = models.BooleanField(default=False)
    volunteerContact = models.BooleanField(default=False)
    volunteerDepts = models.CharField(max_length=1000, blank=True)
    holdType = models.ForeignKey(HoldType, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    parentFirstName = models.CharField(max_length=200, blank=True)
    parentLastName = models.CharField(max_length=200, blank=True)
    parentPhone = models.CharField(max_length=20, blank=True)
    parentEmail = models.CharField(max_length=200, blank=True)
    aslRequest = models.BooleanField(default=False)

    def __str__(self):
      if self is None:
          return "--"
      return '%s %s' % (self.firstName, self.lastName)


class Badge(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event)
    registeredDate = models.DateTimeField(null=True)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    badgeName = models.CharField(max_length=200, blank=True)
    badgeNumber = models.IntegerField(null=True, blank=True)
    printed = models.BooleanField(default=False)

    def getDiscount(self):
      discount = ""
      orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
      for oi in orderItems: 
        if oi.order.discount != None:
          discount = oi.order.discount.codeName
      return discount

    def paidTotal(self):
      total = 0
      orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
      for oi in orderItems: 
          total += oi.order.total
      return Decimal(total)

    def abandoned(self):
        if Staff.objects.filter(attendee=self.attendee).exists():
            return 'Staff'
        if Dealer.objects.filter(attendee=self.attendee).exists():
            return 'Dealer'
        if self.paidTotal() > 0: 
            return 'Paid'
        if self.effectiveLevel():
            return 'Comp'
        return 'Abandoned'

    def effectiveLevel(self):
        level = None
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        for oi in orderItems:
            if not level: level = oi.priceLevel
            elif oi.priceLevel.basePrice > level.basePrice:
                level = oi.priceLevel
        return level

    def save(self, *args, **kwargs):
      if not self.id and not self.registeredDate:
        self.registeredDate = timezone.now()
      return super(Badge, self).save(*args, **kwargs)
    
        

class Staff(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    supervisor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, blank=True)
    twitter = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)
    shirtsize = models.ForeignKey(ShirtSizes, null=True, blank=True, on_delete=models.SET_NULL)    
    timesheetAccess = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    specialSkills = models.TextField(blank=True)
    specialFood = models.TextField(blank=True)
    specialMedical = models.TextField(blank=True)
    contactName = models.CharField(max_length=200, blank=True)
    contactPhone = models.CharField(max_length=200, blank=True)
    contactRelation = models.CharField(max_length=200, blank=True)
    needRoom = models.BooleanField(default=False)
    gender = models.CharField(max_length=50, blank=True)     
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
      return '%s %s' % (self.attendee.firstName, self.attendee.lastName)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee,event=self.event).last()
        return badge


class Dealer(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
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
    emailed = models.BooleanField(default=False)
    asstBreakfast = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
      return '%s %s' % (self.attendee.firstName, self.attendee.lastName)

    def getPartnerCount(self):
      partners = self.partners.split(', ')
      partnerCount = 0
      for part in partners:
        if part.find("name") > -1 and part.split(':')[1].strip() != "":
            partnerCount = partnerCount + 1
      return partnerCount

    def paidTotal(self):
          total = 0
          badge = self.getBadge()
          orderItems = OrderItem.objects.filter(badge=badge)
          for oi in orderItems: 
              if oi.order:
                  total += oi.order.total
          return Decimal(total)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee,event=self.event).last()
        return badge

# Start order tables

class PriceLevelOption(models.Model):
    optionName = models.CharField(max_length=200)
    optionPrice = models.DecimalField(max_digits=6, decimal_places=2)
    optionExtraType = models.CharField(max_length=100, blank=True)
    optionExtraType2 = models.CharField(max_length=100, blank=True)
    optionExtraType3 = models.CharField(max_length=100, blank=True)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def __str__(self):
      return '%s' % (self.optionName)

    def getList(self):
        if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{'name':s.name, 'id':s.id} for s in ShirtSizes.objects.all()]
        else:
            return []
 
class PriceLevel(models.Model):
    name = models.CharField(max_length=100)
    priceLevelOptions = models.ManyToManyField(PriceLevelOption)
    description = models.TextField()
    basePrice = models.DecimalField(max_digits=6, decimal_places=2)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    public = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    group = models.TextField(blank=True)
    emailVIP = models.BooleanField(default=False)
    emailVIPEmails = models.CharField(max_length=400, blank=True, default='')

    def __str__(self):
      return self.name

class Discount(models.Model):
    codeName = models.CharField(max_length=100)
    percentOff = models.IntegerField(null=True)
    amountOff = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    notes = models.TextField(blank=True)
    oneTime = models.BooleanField(default=False)
    used = models.IntegerField(default=0)
    reason = models.CharField(max_length=100, blank=True)

    def __str__(self):
      return self.codeName

    def isValid(self):
        now = timezone.now()
        if self.startDate > now or self.endDate < now:
            return False
        if self.oneTime and self.used > 0:
            return False
        return True

class Order(models.Model):
    CREDIT = 'Credit'
    CASH = 'Cash'
    COMP = 'Comp'
    BILLING_TYPE_CHOICES = ((CREDIT, 'Credit'), (CASH, 'Cash'), (COMP, 'Comp'))
    total = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')
    reference = models.CharField(max_length=50)
    createdDate = models.DateTimeField(auto_now_add=True, null=True)
    settledDate = models.DateTimeField(auto_now_add=True, null=True)
    discount = models.ForeignKey(Discount, null=True, on_delete=models.SET_NULL)
    orgDonation = models.DecimalField(max_digits=8, decimal_places=2, null=True, default=0)
    charityDonation = models.DecimalField(max_digits=8, decimal_places=2, null=True, default=0)
    notes = models.TextField(blank=True)
    billingName = models.CharField(max_length=200, blank=True)
    billingAddress1 = models.CharField(max_length=200, blank=True)
    billingAddress2 = models.CharField(max_length=200, blank=True)
    billingCity = models.CharField(max_length=200, blank=True)
    billingState = models.CharField(max_length=200, blank=True)
    billingCountry = models.CharField(max_length=200, blank=True)
    billingPostal = models.CharField(max_length=20, blank=True)
    billingEmail = models.CharField(max_length=200, blank=True)
    billingType = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default=CREDIT)
    lastFour = models.CharField(max_length=4, blank=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True)
    badge = models.ForeignKey(Badge, null=True)
    priceLevel = models.ForeignKey(PriceLevel)
    enteredBy = models.CharField(max_length=100)
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)

    def getOptions(self):
      return list(AttendeeOptions.objects.filter(orderItem=self))

class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption)
    orderItem = models.ForeignKey(OrderItem)
    optionValue = models.CharField(max_length=200)
    optionValue2 = models.CharField(max_length=200, blank=True)
    optionValue3 = models.CharField(max_length=200, blank=True)

    def getTotal(self):
        if self.option.optionExtraType == "int":
            return int(self.optionValue) * self.option.optionPrice
        return self.option.optionPrice


class BanList(models.Model):
    firstName = models.CharField(max_length=200, blank=True)
    lastName = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=400, blank=True)
