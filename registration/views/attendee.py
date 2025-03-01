import json
import logging
from datetime import date

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import timezone

from registration.models import (
    Attendee,
    Badge,
    BanList,
    Dealer,
    Event,
    PriceLevel,
    Staff,
)

logger = logging.getLogger(__name__)


def get_attendee_age(attendee):
    born = attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


def check_ban_list(firstName, lastName, email):
    ban_check = BanList.objects.filter(
        firstName=firstName, lastName=lastName, email=email
    )
    return ban_check.count() > 0


# moved to views.pricelevels
# def get_price_level_list(levels): 
#     data = [
#         {
#             "name": level.name,
#             "id": level.id,
#             "base_price": level.basePrice.__str__(),
#             "description": level.description,
#             "options": [
#                 {
#                     "name": option.optionName,
#                     "value": option.optionPrice,
#                     "id": option.id,
#                     "required": option.required,
#                     "active": option.active,
#                     "type": option.optionExtraType,
#                     "image": option.getOptionImage(),
#                     "description": option.description,
#                     "list": option.getList(),
#                 }
#                 for option in level.priceLevelOptions.order_by(
#                     "rank", "optionPrice"
#                 ).all()
#             ],
#         }
#         for level in levels
#     ]
#     return data


#deprecated
# def get_price_levels(request): 
#     dealer = request.session.get("dealer_id", -1)
#     staff = request.session.get("staff_id", -1)
#     attendee = request.session.get("attendee_id", -1)
#     # hide any irrelevant price levels if something in session
#     att = None
#     if dealer > 0:
#         deal = Dealer.objects.get(id=dealer)
#         att = deal.attendee
#         event = deal.event
#         badge = Badge.objects.filter(attendee=att, event=event).last()
#     if staff > 0:
#         sta = Staff.objects.get(id=staff)
#         att = sta.attendee
#         event = sta.event
#         badge = Badge.objects.filter(attendee=att, event=event).last()
#     if attendee > 0:
#         att = Attendee.objects.get(id=attendee)
#         badge = Badge.objects.filter(attendee=att).last()

#     now = timezone.now()
#     levels = PriceLevel.objects.filter(
#         public=True, startDate__lte=now, endDate__gte=now
#     ).order_by("basePrice")
#     # if att and badge and badge.effectiveLevel():
#     #    levels = levels.exclude(basePrice__lt=badge.effectiveLevel().basePrice)
#     data = get_price_level_list(levels)
#     return HttpResponse(
#         json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
#     )
