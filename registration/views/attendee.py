from datetime import date

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse

from registration.models import *


def get_attendee_age(attendee):
    born = attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


def checkBanList(firstName, lastName, email):
    banCheck = BanList.objects.filter(
        firstName=firstName, lastName=lastName, email=email
    )
    if banCheck.count() > 0:
        return True
    return False


def getPriceLevelList(levels):
    data = [
        {
            "name": level.name,
            "id": level.id,
            "base_price": level.basePrice.__str__(),
            "description": level.description,
            "options": [
                {
                    "name": option.optionName,
                    "value": option.optionPrice,
                    "id": option.id,
                    "required": option.required,
                    "active": option.active,
                    "type": option.optionExtraType,
                    "image": option.getOptionImage(),
                    "description": option.description,
                    "list": option.getList(),
                }
                for option in level.priceLevelOptions.order_by(
                    "rank", "optionPrice"
                ).all()
            ],
        }
        for level in levels
    ]
    return data


def getMinorPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(
        public=False, startDate__lte=now, endDate__gte=now, name__icontains="minor"
    ).order_by("basePrice")
    data = getPriceLevelList(levels)
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


def getAccompaniedPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(
        public=False,
        startDate__lte=now,
        endDate__gte=now,
        name__icontains="accompanied",
    ).order_by("basePrice")
    data = getPriceLevelList(levels)
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


def getFreePriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(
        public=False, startDate__lte=now, endDate__gte=now, name__icontains="free"
    )
    data = getPriceLevelList(levels)
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


def getPriceLevels(request):
    dealer = request.session.get("dealer_id", -1)
    staff = request.session.get("staff_id", -1)
    attendee = request.session.get("attendee_id", -1)
    # hide any irrelevant price levels if something in session
    att = None
    if dealer > 0:
        deal = Dealer.objects.get(id=dealer)
        att = deal.attendee
        event = deal.event
        badge = Badge.objects.filter(attendee=att, event=event).last()
    if staff > 0:
        sta = Staff.objects.get(id=staff)
        att = sta.attendee
        event = sta.event
        badge = Badge.objects.filter(attendee=att, event=event).last()
    if attendee > 0:
        att = Attendee.objects.get(id=attendee)
        badge = Badge.objects.filter(attendee=att).last()

    now = timezone.now()
    levels = PriceLevel.objects.filter(
        public=True, startDate__lte=now, endDate__gte=now
    ).order_by("basePrice")
    if att and badge and badge.effectiveLevel():
        levels = levels.exclude(basePrice__lt=badge.effectiveLevel().basePrice)
    data = getPriceLevelList(levels)
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


def getAdultPriceLevels(request):
    dealer = request.session.get("dealer_id", -1)
    staff = request.session.get("staff_id", -1)
    attendee = request.session.get("attendee_id", -1)
    # hide any irrelevant price levels if something in session
    att = None
    if dealer > 0:
        deal = Dealer.objects.get(id=dealer)
        att = deal.attendee
        event = deal.event
        badge = Badge.objects.filter(attendee=att, event=event).last()
    if staff > 0:
        sta = Staff.objects.get(id=staff)
        att = sta.attendee
        event = sta.event
        badge = Badge.objects.filter(attendee=att, event=event).last()
    if attendee > 0:
        att = Attendee.objects.get(id=attendee)
        badge = Badge.objects.filter(attendee=att).last()

    now = timezone.now()
    levels = PriceLevel.objects.filter(
        public=True, isMinor=False, startDate__lte=now, endDate__gte=now
    ).order_by("basePrice")
    if att and badge and badge.effectiveLevel():
        levels = levels.exclude(basePrice__lt=badge.effectiveLevel().basePrice)
    data = getPriceLevelList(levels)
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
