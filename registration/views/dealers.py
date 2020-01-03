from datetime import datetime

from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import render

import registration.emails
from registration.models import *
from registration.views.common import get_client_ip, handler, logger
from registration.views.orders import doCheckout, doZeroCheckout, getDiscountTotal


def dealers(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/dealer/dealer-locate.html", context)


def thanksDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealer-thanks.html", context)


def updateDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealer-update.html", context)


def doneDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealer-done.html", context)


def dealerAsst(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/dealer/dealerasst-locate.html", context)


def doneAsstDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealerasst-done.html", context)


def newDealer(request):
    event = Event.objects.get(default=True)
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {"event": event}
    if event.dealerRegStart <= today <= event.dealerRegEnd:
        return render(request, "registration/dealer/dealer-form.html", context)
    return render(request, "registration/dealer/dealer-closed.html", context)


def infoDealer(request):
    event = Event.objects.get(default=True)
    context = {"dealer": None, "event": event}
    try:
        dealerId = request.session["dealer_id"]
    except Exception as e:
        return render(request, "registration/dealer/dealer-payment.html", context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer:
        badge = Badge.objects.filter(
            attendee=dealer.attendee, event=dealer.event
        ).last()
        dealer_dict = model_to_dict(dealer)
        attendee_dict = model_to_dict(dealer.attendee)
        if badge is not None:
            badge_dict = model_to_dict(badge)
        else:
            badge_dict = {}
        table_dict = model_to_dict(dealer.tableSize)

        context = {
            "dealer": dealer,
            "badge": badge,
            "event": dealer.event,
            "jsonDealer": json.dumps(dealer_dict, default=handler),
            "jsonTable": json.dumps(table_dict, default=handler),
            "jsonAttendee": json.dumps(attendee_dict, default=handler),
            "jsonBadge": json.dumps(badge_dict, default=handler),
        }
    return render(request, "registration/dealer/dealer-payment.html", context)


def findDealer(request):
    try:
        postData = json.loads(request.body)
        email = postData["email"]
        token = postData["token"]

        dealer = Dealer.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
        if not dealer:
            return HttpResponseServerError("No Dealer Found " + email)

        request.session["dealer_id"] = dealer.id
        return JsonResponse({"success": True, "message": "DEALER"})
    except Exception as e:
        logger.exception("Error finding dealer. " + email)
        return HttpResponseServerError(str(e))


def findAsstDealer(request):
    try:
        postData = json.loads(request.body)
        email = postData["email"]
        token = postData["token"]

        dealer = Dealer.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
        if not dealer:
            return HttpResponseServerError("No Dealer Found")

        request.session["dealer_id"] = dealer.id
        return JsonResponse({"success": True, "message": "DEALER"})
    except Exception as e:
        logger.exception("Error finding assistant dealer.")
        return HttpResponseServerError(str(e))


def invoiceDealer(request):
    sessionItems = request.session.get("order_items", [])
    sessionDiscount = request.session.get("discount", "")
    if not sessionItems:
        context = {"orderItems": [], "total": 0, "discount": {}}
        request.session.flush()
    else:
        dealerId = request.session.get("dealer_id", -1)
        if dealerId == -1:
            context = {"orderItems": [], "total": 0, "discount": {}}
            request.session.flush()
        else:
            dealer = Dealer.objects.get(id=dealerId)
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            discount = Discount.objects.filter(codeName=sessionDiscount).first()
            total = getDealerTotal(orderItems, discount, dealer)
            context = {
                "orderItems": orderItems,
                "total": total,
                "discount": discount,
                "dealer": dealer,
            }
    event = Event.objects.get(default=True)
    context["event"] = event
    return render(request, "registration/dealer/dealer-checkout.html", context)


def addAsstDealer(request):
    context = {"attendee": None, "dealer": None}
    try:
        dealerId = request.session["dealer_id"]
    except Exception as e:
        return render(request, "registration/dealer/dealerasst-add.html", context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer.attendee:
        assts = list(DealerAsst.objects.filter(dealer=dealer))
        assistants = []
        for dasst in assts:
            assistants.append(model_to_dict(dasst))
        context = {
            "attendee": dealer.attendee,
            "dealer": dealer,
            "asstCount": len(assts),
            "jsonAssts": json.dumps(assistants, default=handler),
        }
    event = Event.objects.get(default=True)
    context["event"] = event
    return render(request, "registration/dealer/dealerasst-add.html", context)


def checkoutAsstDealer(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for checkoutAsstDealer()")
        return JsonResponse({"success": False})
    pbill = postData["billingData"]
    assts = postData["assistants"]
    dealerId = request.session["dealer_id"]
    dealer = Dealer.objects.get(id=dealerId)
    event = Event.objects.get(default=True)

    badge = Badge.objects.filter(attendee=dealer.attendee, event=dealer.event).last()

    priceLevel = badge.effectiveLevel()
    if priceLevel is None:
        return JsonResponse(
            {
                "success": False,
                "message": "Dealer acocunt has not been paid. Please pay for your table before adding assistants.",
            }
        )

    originalPartnerCount = dealer.getPartnerCount()

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    # dealer.partners = assts
    for assistant in assts:
        dasst = DealerAsst(
            dealer=dealer,
            event=event,
            name=assistant["name"],
            email=assistant["email"],
            license=assistant["license"],
        )
        dasst.save()
    partnerCount = dealer.getPartnerCount()

    # FIXME: remove hardcoded costs
    partners = partnerCount - originalPartnerCount
    total = Decimal(45 * partners)
    if pbill["breakfast"]:
        total = total + Decimal(60 * partners)
    ip = get_client_ip(request)

    status, message, order = doCheckout(pbill, total, None, [], [orderItem], 0, 0)

    if status:
        request.session.flush()
        try:
            registration.emails.sendDealerAsstEmail(dealer.id)
        except Exception as e:
            logger.exception("Error emailing DealerAsstEmail.")
            dealerEmail = getDealerEmail()
            return JsonResponse(
                {
                    "success": False,
                    "message": "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact {0} to get your confirmation number.".format(
                        dealerEmail
                    ),
                }
            )
        return JsonResponse({"success": True})
    else:
        orderItem.delete()
        for assistant in assts:
            assistant.delete()
        return JsonResponse({"success": False, "message": message})


def addDealer(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addStaff()")
        return JsonResponse({"success": False})

    pda = postData["attendee"]
    pdd = postData["dealer"]
    evt = postData["event"]
    pdp = postData["priceLevel"]
    event = Event.objects.get(name=evt)

    if "dealer_id" not in request.session:
        return HttpResponseServerError("Session expired")

    dealer = Dealer.objects.get(id=pdd["id"])

    # Update Dealer info
    if not dealer:
        return HttpResponseServerError("Dealer id not found")

    dealer.businessName = pdd["businessName"]
    dealer.website = pdd["website"]
    dealer.logo = pdd["logo"]
    dealer.description = pdd["description"]
    dealer.license = pdd["license"]
    dealer.needPower = pdd["power"]
    dealer.needWifi = pdd["wifi"]
    dealer.wallSpace = pdd["wall"]
    dealer.nearTo = pdd["near"]
    dealer.farFrom = pdd["far"]
    dealer.reception = pdd["reception"]
    dealer.artShow = pdd["artShow"]
    dealer.charityRaffle = pdd["charityRaffle"]
    dealer.breakfast = pdd["breakfast"]
    dealer.willSwitch = pdd["switch"]
    dealer.buttonOffer = pdd["buttonOffer"]
    dealer.asstBreakfast = pdd["asstbreakfast"]
    dealer.event = event

    try:
        dealer.save()
    except Exception as e:
        logger.exception("Error saving dealer record.")
        return HttpResponseServerError(str(e))

    # Update Attendee info
    attendee = Attendee.objects.get(id=pda["id"])
    if not attendee:
        return HttpResponseServerError("Attendee id not found")

    attendee.firstName = pda["firstName"]
    attendee.lastName = pda["lastName"]
    attendee.address1 = pda["address1"]
    attendee.address2 = pda["address2"]
    attendee.city = pda["city"]
    attendee.state = pda["state"]
    attendee.country = pda["country"]
    attendee.postalCode = pda["postal"]
    attendee.phone = pda["phone"]

    try:
        attendee.save()
    except Exception as e:
        logger.exception("Error saving dealer attendee record.")
        return HttpResponseServerError(str(e))

    badge = Badge.objects.get(attendee=attendee, event=event)
    badge.badgeName = pda["badgeName"]

    try:
        badge.save()
    except Exception as e:
        logger.exception("Error saving dealer badge record.")
        return HttpResponseServerError(str(e))

    priceLevel = PriceLevel.objects.get(id=int(pdp["id"]))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp["options"]:
        plOption = PriceLevelOption.objects.get(id=int(option["id"]))
        attendeeOption = AttendeeOptions(
            option=plOption, orderItem=orderItem, optionValue=option["value"]
        )
        attendeeOption.save()

    orderItems = request.session.get("order_items", [])
    orderItems.append(orderItem.id)
    request.session["order_items"] = orderItems

    return JsonResponse({"success": True})


def checkoutDealer(request):
    try:
        sessionItems = request.session.get("order_items", [])
        pdisc = request.session.get("discount", "")
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        orderItem = orderItems[0]
        if "dealer_id" not in request.session:
            return HttpResponseServerError("Session expired")

        dealer = Dealer.objects.get(id=request.session.get("dealer_id"))
        try:
            postData = json.loads(request.body)
        except ValueError as e:
            logger.error("Unable to decode JSON for checkoutDealer()")
            return JsonResponse({"success": False})

        discount = Discount.objects.filter(codeName=pdisc).first()
        subtotal = getDealerTotal(orderItems, discount, dealer)

        if subtotal == 0:

            status, message, order = doZeroCheckout(discount, None, orderItems)
            if not status:
                return JsonResponse({"success": False, "message": message})

            request.session.flush()

            try:
                registration.emails.sendDealerPaymentEmail(dealer, order)
            except Exception as e:
                logger.exception("Error sending DealerPaymentEmail - zero sum.")
                dealerEmail = getDealerEmail()
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact {0}".format(
                            dealerEmail
                        ),
                    }
                )
            return JsonResponse({"success": True})

        porg = Decimal(postData["orgDonation"].strip() or "0.00")
        pcharity = Decimal(postData["charityDonation"].strip() or "0.00")
        if porg < 0:
            porg = 0
        if pcharity < 0:
            pcharity = 0

        total = subtotal + porg + pcharity

        pbill = postData["billingData"]
        ip = get_client_ip(request)
        status, message, order = doCheckout(
            pbill, total, discount, None, orderItems, porg, pcharity
        )

        if status:
            request.session.flush()
            try:
                dealer.resetToken()
                registration.emails.sendDealerPaymentEmail(dealer, order)
            except Exception as e:
                logger.exception("Error sending DealerPaymentEmail. " + request.body)
                dealerEmail = getDealerEmail()
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact {0}".format(
                            dealerEmail
                        ),
                    }
                )
            return JsonResponse({"success": True})
        else:
            order.delete()
            return JsonResponse({"success": False, "message": message})
    except Exception as e:
        logger.exception("Error in dealer checkout.")
        return HttpResponseServerError(str(e))


def addNewDealer(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addNewDealer()")
        return JsonResponse({"success": False})

    try:
        # create attendee from request post
        pda = postData["attendee"]
        pdd = postData["dealer"]
        evt = postData["event"]

        tz = timezone.get_current_timezone()
        birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))
        event = Event.objects.get(name=evt)

        attendee = Attendee(
            firstName=pda["firstName"],
            lastName=pda["lastName"],
            address1=pda["address1"],
            address2=pda["address2"],
            city=pda["city"],
            state=pda["state"],
            country=pda["country"],
            postalCode=pda["postal"],
            phone=pda["phone"],
            email=pda["email"],
            birthdate=birthdate,
            emailsOk=bool(pda["emailsOk"]),
            surveyOk=bool(pda["surveyOk"]),
        )
        attendee.save()

        badge = Badge(attendee=attendee, event=event, badgeName=pda["badgeName"])
        badge.save()

        tablesize = TableSize.objects.get(id=pdd["tableSize"])
        dealer = Dealer(
            attendee=attendee,
            event=event,
            businessName=pdd["businessName"],
            logo=pdd["logo"],
            website=pdd["website"],
            description=pdd["description"],
            license=pdd["license"],
            needPower=pdd["power"],
            needWifi=pdd["wifi"],
            wallSpace=pdd["wall"],
            nearTo=pdd["near"],
            farFrom=pdd["far"],
            tableSize=tablesize,
            chairs=pdd["chairs"],
            reception=pdd["reception"],
            artShow=pdd["artShow"],
            charityRaffle=pdd["charityRaffle"],
            breakfast=pdd["breakfast"],
            willSwitch=pdd["switch"],
            tables=pdd["tables"],
            agreeToRules=pdd["agreeToRules"],
            buttonOffer=pdd["buttonOffer"],
            asstBreakfast=pdd["asstbreakfast"],
        )
        dealer.save()

        partners = pdd["partners"]
        for partner in partners:
            dealerPartner = DealerAsst(
                dealer=dealer,
                event=event,
                name=partner["name"],
                email=partner["email"],
                license=partner["license"],
            )
            dealerPartner.save()

        try:
            registration.emails.sendDealerApplicationEmail(dealer.id)
        except Exception as e:
            logger.exception("Error sending DealerApplicationEmail.")
            dealerEmail = getDealerEmail()
            return JsonResponse(
                {
                    "success": False,
                    "message": "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact {0}.".format(
                        dealerEmail
                    ),
                }
            )
        return JsonResponse({"success": True})

    except Exception as e:
        logger.exception("Error in dealer addition." + request.body)
        return HttpResponseServerError(str(e))


def getTableSizes(request):
    event = Event.objects.get(default=True)
    sizes = TableSize.objects.filter(event=event)
    data = [
        {
            "name": size.name,
            "id": size.id,
            "description": size.description,
            "chairMin": size.chairMin,
            "chairMax": size.chairMax,
            "tableMin": size.tableMin,
            "tableMax": size.tableMax,
            "partnerMin": size.partnerMin,
            "partnerMax": size.partnerMax,
            "basePrice": str(size.basePrice),
        }
        for size in sizes
    ]
    return HttpResponse(json.dumps(data), content_type="application/json")


def getDealerEmail(event=None):
    """
    Retrieves the email address to show on error messages in the dealer
    registration form for a specified event.  If no event specified, uses
    the first default event.  If no email is listed there, returns the
    default of APIS_DEFAULT_EMAIL in settings.py.
    """
    if event is None:
        try:
            event = Event.objects.get(default=True)
        except BaseException:
            return settings.APIS_DEFAULT_EMAIL
    if event.dealerEmail == "":
        return settings.APIS_DEFAULT_EMAIL
    return event.dealerEmail


def getDealerTotal(orderItems, discount, dealer):
    itemSubTotal = 0
    for item in orderItems:
        itemSubTotal = item.priceLevel.basePrice
        for option in item.attendeeoptions_set.all():
            if option.option.optionExtraType == "int":
                if option.optionValue:
                    itemSubTotal += option.option.optionPrice * Decimal(
                        option.optionValue
                    )
            else:
                itemSubTotal += option.option.optionPrice
    partnerCount = dealer.getPartnerCount()
    partnerBreakfast = 0
    if partnerCount > 0 and dealer.asstBreakfast:
        partnerBreakfast = 60 * partnerCount
    wifi = 0
    power = 0
    if dealer.needWifi:
        wifi = 50
    if dealer.needPower:
        power = 0
    paidTotal = dealer.paidTotal()
    if discount:
        itemSubTotal = getDiscountTotal(discount, itemSubTotal)
    total = (
        itemSubTotal
        + 45 * partnerCount
        + partnerBreakfast
        + dealer.tableSize.basePrice
        + wifi
        + power
        - dealer.discount
        - paidTotal
    )
    if total < 0:
        return 0
    return total
