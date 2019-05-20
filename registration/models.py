from __future__ import unicode_literals
import json
import random
import string
from decimal import *
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

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

def content_file_name(instance, filename):
    return '/'.join(['priceleveloption',str(instance.pk),filename])

class PriceLevelOption(models.Model):
    optionName = models.CharField(max_length=200)
    optionPrice = models.DecimalField(max_digits=6, decimal_places=2)
    optionExtraType = models.CharField(max_length=100, blank=True)
    optionExtraType2 = models.CharField(max_length=100, blank=True)
    optionExtraType3 = models.CharField(max_length=100, blank=True)
    optionImage = models.ImageField(upload_to=content_file_name,blank=True,null=True)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    rank = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return '{0} (${1})'.format(self.optionName, self.optionPrice)

    def getList(self):
        if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{'name':s.name, 'id':s.id} for s in ShirtSizes.objects.all()]
        else:
            return []
    def getOptionImage(self):
        if self.optionImage is None:
            return None
        else:
            try:
                return self.optionImage.url
            except ValueError:
                return None

class PriceLevel(models.Model):
    name = models.CharField(max_length=100)
    priceLevelOptions = models.ManyToManyField(PriceLevelOption, blank=True)
    description = models.TextField()
    basePrice = models.DecimalField(max_digits=6, decimal_places=2)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    public = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    group = models.TextField(blank=True)
    emailVIP = models.BooleanField(default=False)
    emailVIPEmails = models.CharField(max_length=400, blank=True, default='')
    isMinor = models.BooleanField(default=False)

    def __str__(self):
      return self.name

class Charity(LookupTable):
    url = models.CharField(max_length=500,
        verbose_name="URL",
        help_text="Charity link",
        blank=True)

class Event(LookupTable):
    dealerRegStart = models.DateTimeField(verbose_name="Dealer Registration Start",
        help_text="Start date and time for dealer applications")
    dealerRegEnd = models.DateTimeField(verbose_name="Dealer Registration End")
    staffRegStart = models.DateTimeField(verbose_name="Staff Registration Start",
        help_text="(Not currently enforced)")
    staffRegEnd = models.DateTimeField(verbose_name="Staff Registration End")
    attendeeRegStart = models.DateTimeField(verbose_name="Attendee Registration Start")
    attendeeRegEnd = models.DateTimeField(verbose_name="Attendee Registration End")
    onlineRegStart = models.DateTimeField("On-site Registration Start",
        help_text="Start time for /registration/onsite form")
    onlineRegEnd = models.DateTimeField(verbose_name="On-site Registration End")
    eventStart = models.DateField(verbose_name="Event Start Date")
    eventEnd = models.DateField(verbose_name="Event End Date")
    default = models.BooleanField(default=False, verbose_name="Default",
        help_text="The first default event will be used as the basis for all current event configuration")
    newStaffDiscount = models.ForeignKey(Discount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='newStaffEvent',
        verbose_name="New Staff Discount",
        help_text="Apply a discount for new staff registrations")
    staffDiscount = models.ForeignKey(Discount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="staffEvent",
        verbose_name="Staff Discount",
        help_text="Apply a discount for any staff registrations")
    dealerDiscount = models.ForeignKey(Discount, null=True, blank=True, 
        on_delete=models.SET_NULL, related_name="dealerEvent",
        verbose_name="Dealer Discount",
        help_text="Apply a discount for any dealer registrations")
    allowOnlineMinorReg = models.BooleanField(default=False,
        verbose_name="Allow online minor registration",
        help_text="Allow registration for anyone age 13 and older online. "
        "Otherwise, registration is restricted to those 18 or older.")
    collectAddress = models.BooleanField(default=True,
        verbose_name="Collect Address",
        help_text="Disable to skip collecting a mailing address for each "
        "attendee.")
    collectBillingAddress = models.BooleanField(default=True,
        verbose_name="Collect Billing Address",
        help_text="Disable to skip collecting a billing address for each "
        "order. Note that a billing address and buyer email is required "
        "to qualify for Square's Chargeback protection.")
    registrationEmail = models.CharField(max_length=200,
        verbose_name="Registration Email",
        help_text="Email to display on error messages for attendee registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    staffEmail = models.CharField(max_length=200,
        verbose_name="Staff Email",
        help_text="Email to display on error messages for staff registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    dealerEmail = models.CharField(max_length=200,
        verbose_name="Dealer Email",
        help_text="Email to display on error messages for dealer registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    badgeTheme = models.CharField(max_length=200,
        verbose_name="Badge Theme",
        help_text="Name of badge theme to use for printing",
        blank=False,
        default='apis')
    codeOfConduct = models.CharField(max_length=500,
        verbose_name="Code of Conduct",
        help_text="Link to code of conduct agreement",
        blank=True,
        default='/code-of-conduct')
    charity = models.ForeignKey(Charity, null=True, blank=True, on_delete=models.SET_NULL)

class TableSize(LookupTable):
    description = models.TextField()
    chairMin = models.IntegerField(default=1)
    chairMax = models.IntegerField(default=1)
    tableMin = models.IntegerField(default=0)
    tableMax = models.IntegerField(default=0)
    partnerMin = models.IntegerField(default=1)
    partnerMax = models.IntegerField(default=1)
    basePrice = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)

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

class TempToken(models.Model):
    token = models.CharField(max_length=200, default=getRegistrationToken)
    email = models.CharField(max_length=200)
    validUntil = models.DateTimeField()
    used = models.BooleanField(default=False)
    usedDate = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

class Attendee(models.Model):
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    postalCode = models.CharField(max_length=20, blank=True)
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
      # FIXME: Why are we afraid of Unicode here?
      try:
        test1 = self.firstName.decode('ascii')
        test2 = self.lastName.decode('ascii')
        return '%s %s' % (self.firstName, self.lastName)
      except:
        return '--attendee--'

class Badge(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registeredDate = models.DateTimeField(null=True)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    badgeName = models.CharField(max_length=200, blank=True)
    badgeNumber = models.IntegerField(null=True, blank=True)
    printed = models.BooleanField(default=False)
    printCount = models.IntegerField(default=0)

    def __str__(self):
        if self.badgeNumber is not None or self.badgeNumber == '':
            return '"{0}" #{1} ({2})'.format(self.badgeName, self.badgeNumber, self.event).encode("utf-8")
        if self.badgeName != '':
            return '"{0}" ({1})'.format(self.badgeName, self.event).encode("utf-8")
        if self.registeredDate is not None:
            return "[Orphan {0}]".format(self.registeredDate)
        return "Badge object {0}".format(self.registrationToken)

    def isMinor(self):
      birthdate = self.attendee.birthdate
      eventdate = self.event.eventStart
      age_at_event = eventdate.year - birthdate.year - ((eventdate.month, eventdate.day) < (birthdate.month, birthdate.day))
      if age_at_event < 18: 
        return True
      return False

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
          if oi.order.billingType != Order.UNPAID:
              total += oi.order.total
      return Decimal(total)

    @property
    def abandoned(self):
        if Staff.objects.filter(attendee=self.attendee).exists():
            return 'Staff'
        if Dealer.objects.filter(attendee=self.attendee).exists():
            return 'Dealer'
        if self.paidTotal() > 0:
            return 'Paid'
        level = self.effectiveLevel()
        if level == 'Unpaid':
            return 'Unpaid'
        if level:
            return 'Comp'
        return 'Abandoned'

    def effectiveLevel(self):
        level = None
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        for oi in orderItems:
            if oi.order.billingType == Order.UNPAID:
                return 'Unpaid'
            if not level:
                level = oi.priceLevel
            elif oi.priceLevel.basePrice > level.basePrice:
                level = oi.priceLevel
        return level

    def getOrderItems(self):
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        return orderItems

    def getOrder(self):
        oi = self.getOrderItems().first()
        return oi.order

    def save(self, *args, **kwargs):
      if not self.id and not self.registeredDate:
        self.registeredDate = timezone.now()
      return super(Badge, self).save(*args, **kwargs)



class Staff(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
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
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    checkedIn = models.BooleanField(default=False)

    def __str__(self):
      return '%s %s' % (self.attendee.firstName, self.attendee.lastName)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee,event=self.event).last()
        return badge

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


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
    tableSize = models.ForeignKey(TableSize, on_delete=models.SET_NULL, null=True)
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
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    logo = models.CharField(max_length=500, blank=True)

    def __str__(self):
      return '%s %s' % (self.attendee.firstName, self.attendee.lastName)

    def getPartnerCount(self):
      partnercount = self.dealerasst_set.count()
      return partnercount

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

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


class DealerAsst(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    name = models.CharField(max_length=400)
    email = models.CharField(max_length=200)
    license = models.CharField(max_length=50)
    sent = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Start order tables

class Cart(models.Model):
    ATTENDEE = 'Attendee'
    STAFF = 'Staff'
    DEALER = 'Dealer'
    ASST = 'Dealer Assistant'
    FORM_CHOICES = ((ATTENDEE, 'Attendee'), (STAFF, 'Staff'), (DEALER, 'Dealer'), (ASST, 'Dealer Assistant'))
    token = models.CharField(max_length=200, blank=True, null=True)
    form = models.CharField(max_length=50, choices=FORM_CHOICES)
    formData = models.TextField()
    formHeaders = models.TextField()
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)
    transferedDate = models.DateTimeField(null=True)

    def __str__(self):
        return "{0} {1}".format(self.form, self.enteredDate)

class Order(models.Model):
    UNPAID = 'Unpaid'
    CREDIT = 'Credit'
    CASH = 'Cash'
    COMP = 'Comp'
    BILLING_TYPE_CHOICES = ((UNPAID, 'Unpaid'), (CREDIT, 'Credit'), (CASH, 'Cash'), (COMP, 'Comp'))
    total = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')
    reference = models.CharField(max_length=50)
    createdDate = models.DateTimeField(auto_now_add=True, null=True)
    settledDate = models.DateTimeField(auto_now_add=True, null=True)
    discount = models.ForeignKey(Discount, null=True, on_delete=models.SET_NULL, blank=True)
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
    apiData = models.TextField(blank=True)

    def __str__(self):
        return "${0} {1} ({2}) [{3}]".format(
            self.total,
            self.billingType,
            self.status,
            self.reference)

    class Meta:
        permissions = (
            ("issue_refund", "Can create refunds"),
        )

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, null=True, on_delete=models.CASCADE)
    priceLevel = models.ForeignKey(PriceLevel, null=True, on_delete=models.SET_NULL)
    enteredBy = models.CharField(max_length=100)
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)

    def getOptions(self):
      return list(AttendeeOptions.objects.filter(orderItem=self).order_by('option__optionName'))

    def __str__(self):
        try:
            return '{} (${}) - "{}"'.format(
                self.order.status,
                self.order.total,
                self.badge.badgeName,
                ).encode("utf-8")
        except:
            try:
                return 'Incomplete from {}: "{}" ({})'.format(
                    self.enteredBy,
                    self.badge.badgeName,
                    self.priceLevel).encode("utf-8")
            except:
                return "OrderItem object"

class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption, on_delete=models.CASCADE)
    orderItem = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    optionValue = models.CharField(max_length=200)
    optionValue2 = models.CharField(max_length=200, blank=True)
    optionValue3 = models.CharField(max_length=200, blank=True)

    def getTotal(self):
        if self.option.optionExtraType == "int":
            return int(self.optionValue) * self.option.optionPrice
        return self.option.optionPrice

    def __str__(self):
        #return "[{0}] - {1}".format(self.orderItem.decode("utf-8"), 1).encode("utf-8")
        return "[{0}] - {1}".format(str(self.orderItem).decode("utf-8"), self.option).encode("utf-8")


class BanList(models.Model):
    firstName = models.CharField(max_length=200, blank=True)
    lastName = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=400, blank=True)
    reason = models.TextField(blank=True)

class Firebase(models.Model):
    token = models.CharField(max_length=500)
    name = models.CharField(max_length=100)
    closed = models.BooleanField(default=False)
    cashdrawer = models.BooleanField(default=False)

class Cashdrawer(models.Model):
    OPEN = 'Open'
    CLOSE = 'Close'
    TRANSACTION = 'Transaction'
    DEPOSIT = 'Deposit'
    ACTION_CHOICES = ((OPEN, 'Open'), (CLOSE, 'Close'), (TRANSACTION, 'Transaction'), (DEPOSIT, 'Deposit'))
    timestamp = models.DateTimeField(auto_now_add=True)
    # Action: one of - ['OPEN', 'CLOSE', 'TXN', 'DEPOSIT']
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default=OPEN)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    tendered = models.DecimalField(max_digits=8, decimal_places=2, blank=True, default=0)
    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True
        )

# vim: ts=4 sts=4 sw=4 expandtab smartindent
