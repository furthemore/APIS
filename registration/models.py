import random
import string
from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# Lookup and supporting tables.
class LookupTable(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class HoldType(LookupTable):
    pass


def get_hold_type(hold_name) -> HoldType:
    try:
        dispute_hold = HoldType.objects.get(name=hold_name)
    except HoldType.DoesNotExist:
        dispute_hold = HoldType(name=hold_name)
        dispute_hold.save()
    return dispute_hold


class ShirtSizes(LookupTable):
    class Meta:
        db_table = "registration_shirt_sizes"
        verbose_name_plural = "Shirt sizes"


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

    @property
    def status(self):
        now = timezone.now()
        if self.startDate > now:
            return "Inactive"
        if self.endDate < now:
            return "Expired"
        if self.oneTime and self.used > 0:
            return "Consumed"
        return "Active"


def content_file_name(instance, filename):
    return "/".join(["priceleveloption", str(instance.pk), filename])


class PriceLevelOption(models.Model):
    optionName = models.CharField(max_length=200)
    optionPrice = models.DecimalField(max_digits=6, decimal_places=2)
    optionExtraType = models.CharField(
        max_length=100,
        blank=True,
        choices=[("int", "Quantity"), ("bool", "Yes/No"), ("ShirtSizes", "Shirt Size"), ("string", "String")],
    )
    optionExtraType2 = models.CharField(max_length=100, blank=True)
    optionExtraType3 = models.CharField(max_length=100, blank=True)
    optionImage = models.ImageField(upload_to=content_file_name, blank=True, null=True)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    rank = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "registration_price_level_option"
        verbose_name = "Price level option"
        verbose_name_plural = "Price level options (merchandise)"

    def __str__(self):
        return "{0} (${1})".format(self.optionName, self.optionPrice)

    def getList(self):
        if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{"name": s.name, "id": s.id} for s in ShirtSizes.objects.all()]
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
    emailVIPEmails = models.CharField(max_length=400, blank=True, default="")
    isMinor = models.BooleanField(default=False)

    class Meta:
        db_table = "registration_price_level"

    def __str__(self):
        return self.name


class Charity(LookupTable):
    url = models.CharField(
        max_length=500, verbose_name="URL", help_text="Charity link", blank=True
    )
    donations = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="External donations to add to metrics",
    )

    class Meta:
        verbose_name_plural = "Charities"


class Venue(models.Model):
    name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    postalCode = models.CharField(max_length=20, blank=True)
    website = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.name


class BadgeTemplate(models.Model):
    name = models.CharField(max_length=100)
    template = models.TextField()
    paperWidth = models.CharField(max_length=10, null=True, verbose_name="Paper Width")
    paperHeight = models.CharField(max_length=10, null=True, verbose_name="Paper Height")
    marginTop = models.CharField(max_length=10, null=True, verbose_name = "Margin Top")
    marginBottom = models.CharField(max_length=10, null=True, verbose_name = "Margin Bottom")
    marginLeft = models.CharField(max_length=10, null=True, verbose_name="Margin Left")
    marginRight = models.CharField(max_length=10, null=True, verbose_name = "Margin Right")
    landscape = models.BooleanField(default=True)
    scale = models.FloatField(default=1.0)

    def __str__(self):
        return str(self.name)


class Event(LookupTable):
    dealerRegStart = models.DateTimeField(
        verbose_name="Dealer Registration Start",
    )
    dealerRegEnd = models.DateTimeField(verbose_name="Dealer Registration End")
    staffRegStart = models.DateTimeField(
        verbose_name="Staff Registration Start",
    )
    staffRegEnd = models.DateTimeField(verbose_name="Staff Registration End")
    attendeeRegStart = models.DateTimeField(
        verbose_name="Online Attendee Registration Start"
    )
    attendeeRegEnd = models.DateTimeField(
        verbose_name="Online Attendee Registration End"
    )
    onsiteRegStart = models.DateTimeField(
        "On-Site Registration Start",
        help_text="Start time for /registration/onsite form",
    )
    onsiteRegEnd = models.DateTimeField(verbose_name="On-Site Registration End")
    eventStart = models.DateField(verbose_name="Event Start Date")
    eventEnd = models.DateField(verbose_name="Event End Date")
    default = models.BooleanField(
        default=False,
        verbose_name="Default",
        help_text="The first default event will be used as the basis for all current event configuration",
    )
    venue = models.ForeignKey(
        Venue,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    defaultBadgeTemplate = models.ForeignKey(
        BadgeTemplate,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Badge Template",
    )
    newStaffDiscount = models.ForeignKey(
        Discount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="newStaffEvent",
        verbose_name="New Staff Discount",
        help_text="Apply a discount for new staff registrations",
    )
    staffDiscount = models.ForeignKey(
        Discount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staffEvent",
        verbose_name="Staff Discount",
        help_text="Apply a discount for any staff registrations",
    )
    dealerDiscount = models.ForeignKey(
        Discount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dealerEvent",
        verbose_name="Dealer Discount",
        help_text="Apply a discount for any dealer registrations",
    )
    assistantDiscount = models.ForeignKey(
        Discount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assistantEvent",
        verbose_name="Dealer Assistant Discount",
        help_text="Apply a discount for any dealer assistant registrations",
    )
    allowOnlineMinorReg = models.BooleanField(
        default=False,
        verbose_name="Allow online minor registration",
        help_text="Allow registration for anyone age 13 and older online. "
        "Otherwise, registration is restricted to those 18 or older.",
    )
    collectAddress = models.BooleanField(
        default=True,
        verbose_name="Collect Address",
        help_text="Disable to skip collecting a mailing address for each " "attendee.",
    )
    collectBillingAddress = models.BooleanField(
        default=True,
        verbose_name="Collect Billing Address",
        help_text="Disable to skip collecting a billing address for each "
        "order. Note that a billing address and buyer email is required "
        "to qualify for Square's Chargeback protection.",
    )
    registrationEmail = models.CharField(
        max_length=200,
        verbose_name="Registration Email",
        help_text="Email to display on error messages for attendee registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL,
    )
    staffEmail = models.CharField(
        max_length=200,
        verbose_name="Staff Email",
        help_text="Email to display on error messages for staff registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL,
    )
    dealerEmail = models.CharField(
        max_length=200,
        verbose_name="Dealer Email",
        help_text="Email to display on error messages for dealer registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL,
    )
    badgeTheme = models.CharField(
        max_length=200,
        verbose_name="Badge Theme",
        help_text="Name of badge theme to use for printing",
        blank=False,
        default="apis",
    )
    codeOfConduct = models.CharField(
        max_length=500,
        verbose_name="Code of Conduct",
        help_text="Link to code of conduct agreement",
        blank=True,
        default="/code-of-conduct",
    )
    websiteUrl = models.CharField(
        max_length=500,
        verbose_name="Website URL",
        help_text="URL to the homepage for the convention's primary website.",
        blank=True,
    )
    charity = models.ForeignKey(
        Charity, null=True, blank=True, on_delete=models.SET_NULL
    )
    donations = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="External donations to add to metrics ",
    )
    dealerWifi = models.BooleanField(
        default=True,
        verbose_name="Dealer Wifi",
        help_text="Include option to purchase Wifi on dealers form",
    )
    dealerWifiPrice = models.DecimalField(
        decimal_places=2, max_digits=6, default=50, verbose_name="Wifi Price"
    )
    dealerPartnerPrice = models.DecimalField(
        decimal_places=2, max_digits=6, default=55, verbose_name="Partner Price"
    )


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

    class Meta:
        db_table = "registration_table_size"

    def __str__(self):
        if self.event is None:
            return self.name
        return f"{self.name} {self.event.name}"


class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# End lookup and supporting tables


def get_token(length):
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def getRegistrationToken():
    return get_token(15)


class TempToken(models.Model):
    token = models.CharField(max_length=200, default=getRegistrationToken)
    email = models.CharField(max_length=200)
    ignore_time_window = models.BooleanField(
        default=False,
        verbose_name="Ignore Registration Time Window",
        help_text="Enabling this option will allow this invite code to disregard the open and close date and time specified in the event. The Valid Until setting on this form will still apply",
    )
    validUntil = models.DateTimeField()
    used = models.BooleanField(default=False)
    usedDate = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    class Meta:
        db_table = "registration_temp_token"

    def __str__(self):
        return self.token


class Attendee(models.Model):
    firstName = models.CharField("Legal First Name", max_length=200)
    preferredName = models.CharField("Preferred First Name", max_length=200, blank=True)
    lastName = models.CharField("Legal Last Name", max_length=200)
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
    holdType = models.ForeignKey(
        HoldType, null=True, blank=True, on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    parentFirstName = models.CharField(max_length=200, blank=True)
    parentLastName = models.CharField(max_length=200, blank=True)
    parentPhone = models.CharField(max_length=20, blank=True)
    parentEmail = models.CharField(max_length=200, blank=True)
    aslRequest = models.BooleanField(default=False)

    def getFirst(self):
        if not self.preferredName:
            return self.firstName
        else:
            return self.preferredName

    getFirst.short_description = "First Name"

    def __str__(self):
        if self is None:
            return "--"
        return f"{self.getFirst()} {self.lastName}"


def badge_signature_svg_path(instance, filename):
    return "event_{0}/badge_{1}/sig_svg_{2}".format(
        instance.event.id, instance.id, filename
    )


def badge_signature_bitmap_path(instance, filename):
    return "event_{0}/badge_{1}/sig_bmp_{2}".format(
        instance.event.id, instance.id, filename
    )


class Badge(models.Model):
    ABANDONED = "Abandoned"
    COMP = "Comp"
    DEALER = "Dealer"
    PAID = "Paid"
    STAFF = "Staff"
    UNPAID = "Unpaid"
    attendee = models.ForeignKey(
        Attendee, null=True, blank=True, on_delete=models.CASCADE
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registeredDate = models.DateTimeField(null=True)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    badgeName = models.CharField(max_length=200, blank=True)
    badgeNumber = models.IntegerField(null=True, blank=True)
    printed = models.BooleanField(default=False)
    printCount = models.IntegerField(default=0)
    signature_svg = models.TextField(null=True, blank=True)
    signature_bitmap = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.badgeNumber is not None or self.badgeNumber == "":
            return '"{0}" #{1} ({2})'.format(
                self.badgeName, self.badgeNumber, self.event
            )
        if self.badgeName != "":
            return '"{0}" ({1})'.format(self.badgeName, self.event)
        if self.registeredDate is not None:
            return "[Orphan {0}]".format(self.registeredDate)
        return "Badge object {0}".format(self.registrationToken)

    def isMinor(self):
        birthdate = self.attendee.birthdate
        eventdate = self.event.eventStart
        age_at_event = (
            eventdate.year
            - birthdate.year
            - ((eventdate.month, eventdate.day) < (birthdate.month, birthdate.day))
        )
        if age_at_event < 18:
            return True
        return False

    def getDiscount(self):
        discount = ""
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        for oi in orderItems:
            if oi.order.discount is not None:
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
            return Badge.STAFF
        if Dealer.objects.filter(attendee=self.attendee).exists():
            return Badge.DEALER
        if self.paidTotal() > 0:
            return Badge.PAID
        level = self.effectiveLevel()
        if level == Badge.UNPAID:
            return Badge.UNPAID
        if level:
            return Badge.COMP
        return Badge.ABANDONED

    def effectiveLevel(self):
        level = None
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        for oi in orderItems:
            if oi.order.billingType == Order.UNPAID:
                return Badge.UNPAID
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
    attendee = models.ForeignKey(
        Attendee, null=True, blank=True, on_delete=models.CASCADE
    )
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )
    supervisor = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=200, blank=True)
    twitter = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)
    shirtsize = models.ForeignKey(
        ShirtSizes, null=True, blank=True, on_delete=models.SET_NULL
    )
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

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        if self.attendee:
            return "%s %s" % (self.attendee.firstName, self.attendee.lastName)
        return f"<Staff(registrationToken={self.registrationToken})>"

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee, event=self.event).last()
        return badge

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


class Dealer(models.Model):
    attendee = models.ForeignKey(
        Attendee, null=True, blank=True, on_delete=models.SET_NULL
    )
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
        if self.attendee:
            return "%s %s" % (self.attendee.firstName, self.attendee.lastName)
        return "<Dealer(orphan)>"

    def getPartnerCount(self):
        partnercount = self.dealerasst_set.count()
        return partnercount

    def getUnpaidPartnerCount(self):
        unpaidpartnercount = self.dealerasst_set.all().filter(paid=False).count()
        return unpaidpartnercount

    def paidTotal(self):
        total = 0
        badge = self.getBadge()
        orderItems = OrderItem.objects.filter(badge=badge)
        for oi in orderItems:
            if oi.order:
                total += oi.order.total
        return Decimal(total)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee, event=self.event).last()
        return badge

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


class DealerAsst(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    attendee = models.ForeignKey(
        Attendee, null=True, blank=True, on_delete=models.CASCADE
    )
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    name = models.CharField(max_length=400)
    email = models.CharField(max_length=200)
    license = models.CharField(max_length=50)
    sent = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        db_table = "registration_dealer_asst"
        verbose_name = "Dealer assistant"
        verbose_name_plural = "Dealer assistants"

    def __str__(self):
        return self.name


# Start order tables


class Cart(models.Model):
    ATTENDEE = "Attendee"
    STAFF = "Staff"
    DEALER = "Dealer"
    ASST = "Dealer Assistant"
    FORM_CHOICES = (
        (ATTENDEE, "Attendee"),
        (STAFF, "Staff"),
        (DEALER, "Dealer"),
        (ASST, "Dealer Assistant"),
    )
    token = models.CharField(max_length=200, blank=True, null=True)
    form = models.CharField(max_length=50, choices=FORM_CHOICES)
    formData = models.TextField()
    formHeaders = models.TextField()
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)
    transferedDate = models.DateTimeField(null=True)

    def __str__(self):
        return "{0} {1}".format(self.form, self.enteredDate)


class Order(models.Model):
    UNPAID = "Unpaid"
    CREDIT = "Credit"
    CASH = "Cash"
    COMP = "Comp"
    BILLING_TYPE_CHOICES = (
        (UNPAID, "Unpaid"),
        (CREDIT, "Credit"),
        (CASH, "Cash"),
        (COMP, "Comp"),
    )
    PENDING = "Pending"  # Card was captured and authorized, but not yet completed via settlement
    CAPTURED = "Captured"  # Card details were captured, but no online authorization was performed
    COMPLETED = "Completed"  # Card was captured and [later] settled
    FAILED = "Failed"  # Card was rejected by online authorization
    REFUNDED = "Refunded"
    REFUND_PENDING = "Refund Pending"
    DISPUTE_EVIDENCE_REQUIRED = (
        "Dispute Evidence Required"  # Initial state of a dispute with evidence required
    )
    DISPUTE_PROCESSING = "Dispute Processing"  # Dispute evidence has been submitted and the bank is processing
    DISPUTE_WON = "Dispute Won"  # The bank has completed processing the dispute and the seller has won
    DISPUTE_LOST = "Dispute Lost"  # The bank has completed processing the dispute and the seller has lost
    DISPUTE_ACCEPTED = "Dispute Accepted"  # The seller has accepted the dispute
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (CAPTURED, "Captured"),
        (COMPLETED, "Completed"),
        (REFUNDED, "Refunded"),
        (REFUND_PENDING, "Refund Pending"),
        (FAILED, "Failed"),
        (DISPUTE_EVIDENCE_REQUIRED, "Dispute Evidence Required"),
        (DISPUTE_PROCESSING, "Dispute Processing"),
        (DISPUTE_WON, "Dispute Won"),
        (DISPUTE_LOST, "Dispute Lost"),
        (DISPUTE_ACCEPTED, "Dispute Accepted"),
    )
    # Maps Square dispute status to above status choices
    DISPUTE_STATUS_MAP = {
        "EVIDENCE_REQUIRED": DISPUTE_EVIDENCE_REQUIRED,
        "PROCESSING": DISPUTE_PROCESSING,
        "WON": DISPUTE_WON,
        "LOST": DISPUTE_LOST,
        "ACCEPTED": DISPUTE_ACCEPTED,
        # Not certain what these states are for?
        "INQUIRY_EVIDENCE_REQUIRED": DISPUTE_EVIDENCE_REQUIRED,
        "INQUIRY_PROCESSING": DISPUTE_PROCESSING,
        "INQUIRY_CLOSED": DISPUTE_WON,
    }
    total = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PENDING)
    reference = models.CharField(max_length=50)
    createdDate = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name="Created Date"
    )
    settledDate = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name="Settled Date"
    )
    discount = models.ForeignKey(
        Discount, null=True, on_delete=models.SET_NULL, blank=True
    )
    orgDonation = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default=0,
        verbose_name="Organization Donation",
    )
    charityDonation = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default=0,
        verbose_name="Charity Donation",
    )
    notes = models.TextField(blank=True)
    billingName = models.CharField(max_length=200, blank=True, verbose_name="Name")
    billingAddress1 = models.CharField(
        max_length=200, blank=True, verbose_name="Address 1"
    )
    billingAddress2 = models.CharField(
        max_length=200, blank=True, verbose_name="Address 2"
    )
    billingCity = models.CharField(max_length=200, blank=True, verbose_name="City")
    billingState = models.CharField(max_length=200, blank=True, verbose_name="State")
    billingCountry = models.CharField(
        max_length=200, blank=True, verbose_name="Country"
    )
    billingPostal = models.CharField(
        max_length=20, blank=True, verbose_name="Postal Code"
    )
    billingEmail = models.CharField(max_length=200, blank=True, verbose_name="Email")
    billingType = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default=CREDIT,
        verbose_name="Billing Type",
    )
    lastFour = models.CharField(max_length=4, blank=True, verbose_name="Last 4")
    apiData = models.JSONField(null=True)
    onsite_reference = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return "${0} {1} ({2}) [{3}]".format(
            self.total, self.billingType, self.status, self.reference
        )

    class Meta:
        permissions = (
            ("issue_refund", "Can create refunds"),
            ("cash", "Can handle cash transactions"),
            ("cash_admin", "Can open and close cash drawer amounts (manager)"),
            ("discount", "Can create discounts of arbitrary amount"),
        )


class PaymentWebhookNotification(models.Model):
    integration = models.CharField(max_length=50, default="square")
    event_id = models.UUIDField(unique=True)
    event_type = models.CharField(max_length=50, default="")
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    body = models.JSONField("Webhook body")
    headers = models.JSONField("Webhook headers")

    def __str__(self):
        return f"{self.integration} {self.event_type} {self.event_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, null=True, on_delete=models.CASCADE)
    priceLevel = models.ForeignKey(PriceLevel, null=True, on_delete=models.SET_NULL)
    enteredBy = models.CharField(max_length=100)
    enteredDate = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "registration_order_item"

    def getOptions(self):
        return list(
            AttendeeOptions.objects.filter(orderItem=self).order_by(
                "option__optionName"
            )
        )

    def __str__(self):
        try:
            return '{} (${}) - "{}"'.format(
                self.order.status,
                self.order.total,
                self.badge.badgeName,
            )
        except BaseException:
            try:
                return 'Incomplete from {}: "{}" ({})'.format(
                    self.enteredBy, self.badge.badgeName, self.priceLevel
                )
            except BaseException:
                return "OrderItem object"


class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption, on_delete=models.CASCADE)
    orderItem = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    optionValue = models.CharField(max_length=200)
    optionValue2 = models.CharField(max_length=200, blank=True)
    optionValue3 = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "registration_attendee_options"
        verbose_name = "Attendee option"
        verbose_name_plural = "Attendee options"

    def getTotal(self):
        if self.option.optionExtraType == "int":
            return int(self.optionValue) * self.option.optionPrice
        return self.option.optionPrice

    def __str__(self):
        # return "[{0}] - {1}".format(self.orderItem.decode("utf-8"), 1).encode("utf-8")
        return "[{0}] - {1}".format(str(self.orderItem), self.option)


class BanList(models.Model):
    firstName = models.CharField(max_length=200, blank=True)
    lastName = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=400, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = "registration_ban_list"
        verbose_name_plural = "Ban list"


class Firebase(models.Model):
    token = models.CharField(max_length=500, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    closed = models.BooleanField(default=False)
    cashdrawer = models.BooleanField(default=False)
    printer_url = models.CharField(max_length=500, null=True, blank=True)
    background_color = models.CharField(max_length=10, default="#0099cc")
    foreground_color = models.CharField(max_length=10, default="#ffffff")
    print_via_mqtt = models.BooleanField(default=False, verbose_name="Print via MQTT")
    webview = models.CharField(
        max_length=500, null=True, blank=True, default=settings.REGISTER_DEFAULT_WEBVIEW
    )

    def __str__(self):
        return str(self.name)


class Cashdrawer(models.Model):
    OPEN = "Open"  # drawer opens
    CLOSE = "Close"  # drawer closes
    TRANSACTION = "Transaction"  # normal cash transaction
    DEPOSIT = "Deposit"  # additional cash (eg, change) added to drawer
    DROP = "Drop"  # removed excess cash from drawer and added to safe
    PICKUP = "Pickup"  # cash removed from drawer custody by cash office
    ADJUSTMENT = "Adjustment"  # an adjustment made when the count is known to be off, to reset the counters
    ACTION_CHOICES = (
        (OPEN, "Open"),
        (CLOSE, "Close"),
        (TRANSACTION, "Transaction"),
        (DEPOSIT, "Deposit"),
        (DROP, "Drop"),
        (PICKUP, "Pickup"),
        (ADJUSTMENT, "Adjustment"),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    # Action: one of - ['OPEN', 'CLOSE', 'TRANSACTION', 'DEPOSIT', 'DROP', 'PICKUP']
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default=OPEN)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    tendered = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, default=0
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    position = models.ForeignKey(
        Firebase,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="firebase_cashdrawer",
    )


class ReservedBadgeNumbers(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    badgeNumber = models.IntegerField()
    priceLevel = models.ForeignKey(
        PriceLevel, null=True, blank=True, on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return "<Reserved Badge Number({0}, event={1})>".format(
            self.event, self.badgeNumber
        )

    class Meta:
        db_table = "registration_reserved_badge_numbers"
        verbose_name_plural = "Reserved Badge Numbers"


# vim: ts=4 sts=4 sw=4 expandtab smartindent
