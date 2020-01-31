from datetime import datetime

from django.shortcuts import render
from ordering import getTotal

from registration.models import *


def onsite(request):
    event = Event.objects.get(default=True)
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {"event": event}
    if event.onlineRegStart <= today <= event.onlineRegEnd:
        return render(request, "registration/onsite.html", context)
    return render(request, "registration/closed.html", context)


def onsiteCart(request):
    sessionItems = request.session.get("cart_items", [])
    cartItems = list(Cart.objects.filter(id__in=sessionItems))
    orderItems = request.session.get("order_items", [])
    discount = request.session.get("discount", "")

    if not cartItems:
        context = {"orderItems": [], "total": 0}
        request.session.flush()
    else:
        cartItems = list(Cart.objects.filter(id__in=sessionItems))
        orderItems = []
        if discount:
            discount = Discount.objects.filter(codeName=discount)
            if discount.count() > 0:
                discount = discount.first()
        total, total_discount = getTotal(cartItems, [], discount)

        hasMinors = False
        for cart in cartItems:
            cartJson = json.loads(cart.formData)
            pda = cartJson["attendee"]
            try:
                event = Event.objects.get(name=cartJson["event"])
            except Event.DoesNotExist:
                event = Event.objects.get(default=True)
            evt = event.eventStart
            tz = timezone.get_current_timezone()
            try:
                birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))
            except ValueError:
                birthdate = tz.localize(datetime.strptime("2000-01-01", "%Y-%m-%d"))

            age_at_event = (
                evt.year
                - birthdate.year
                - ((evt.month, evt.day) < (birthdate.month, birthdate.day))
            )
            if age_at_event < 18:
                hasMinors = True

            pdp = cartJson["priceLevel"]
            priceLevel = PriceLevel.objects.get(id=pdp["id"])
            pdo = pdp["options"]
            options = []
            for option in pdo:
                dataOption = {}
                optionData = PriceLevelOption.objects.get(id=option["id"])
                if optionData.optionExtraType == "int":
                    if option["value"]:
                        itemTotal = optionData.optionPrice * Decimal(option["value"])
                        total_ = {
                            "name": optionData.optionName,
                            "number": option["value"],
                            "total": itemTotal,
                        }
                        dataOption = total_
                else:
                    itemTotal = optionData.optionPrice
                    dataOption = {"name": optionData.optionName, "total": itemTotal}
                options.append(dataOption)
            orderItem = {
                "id": cart.id,
                "attendee": pda,
                "priceLevel": priceLevel,
                "options": options,
            }
            orderItems.append(orderItem)

        if event is None:
            event = Event.objects.get(default=True)
        context = {
            "event": event,
            "orderItems": orderItems,
            "total": total,
            "total_discount": total_discount,
            "discount": discount,
            "hasMinors": hasMinors,
        }
    return render(request, "registration/onsite-checkout.html", context)


def onsiteDone(request):
    context = {}
    request.session.flush()
    return render(request, "registration/onsite-done.html", context)