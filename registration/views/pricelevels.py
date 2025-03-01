import json
from datetime import date
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from registration.models import Event, PriceLevel
from django.utils import timezone

def format_price_level_list(levels):
    data = [
        {
            "name": level.name,
            "id": level.id,
            "base_price": level.basePrice.__str__(),
            "description": level.description,
            "accompanied": level.accompanied,
            "is_minor": level.isMinor,
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


@csrf_exempt
def get_price_levels(request):
    current_event = Event.objects.get(default=True)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            response = {
                'status': 'error',
                'message': 'Invalid JSON data'
            }
            return JsonResponse(response, status=400)

        try:
            dob = date(int(data.get('year')), int(data.get('month')), int(data.get('day')))
            form_type = data.get('form_type')
        except:
            response = {
                'status': 'error',
                'message': 'Invalid birthdate or form_type'
            }
            return JsonResponse(response, status=400)

        age_at_event = (
                current_event.eventStart.year
                - dob.year
                - ((current_event.eventStart.month, current_event.eventStart.day) < (dob.month, dob.day))
            )
        
        now = timezone.now()
        age_appropriate_levels = PriceLevel.objects.filter(
            Q(public=True) & Q(startDate__lte=now) & Q(endDate__gte=now) & Q(min_age__lte=age_at_event) &
            (Q(max_age__gte=age_at_event) | Q(max_age__isnull=True))
            ).order_by("basePrice")
        
        match form_type:
            case "staff":
                available_levels = age_appropriate_levels.filter(available_to_staff=True)
            case "marketplace":
                available_levels = age_appropriate_levels.filter(available_to_marketplace=True)
            case _:
                available_levels = age_appropriate_levels.filter(available_to_attendee=True) #probably tighten this up at some point

        data = format_price_level_list(available_levels)

        return JsonResponse(data, safe=False)

    else:
        response = {
            'status': 'error',
            'message': 'Only POST requests are allowed'
        }
    return JsonResponse(response, status=400)