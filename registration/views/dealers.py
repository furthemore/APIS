import json
import logging
from datetime import datetime

from django.forms import model_to_dict
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse

import registration.emails
from registration.models import *

from .common import clear_session, get_client_ip, handler, logger
from .ordering import doCheckout, doZeroCheckout, getDiscountTotal

logger = logging.getLogger(__name__)


def dealers(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/dealer/dealer-locate.html", context)


def thanksDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealer-thanks.html", context)


def doneDealer(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/dealer/dealer-done.html", context)


def find_dealer_to_add_assistant(request, guid):
    event = Event.objects.get(default=True)
    context = {
        "token": guid,
        "event": event,
        "next": reverse("registration:find_dealer_to_add_assistant_post"),
    }
    return render(request, "registration/dealer/dealerasst-locate.html", context)


def dealerAsst(request, guid):
    event = Event.objects.get(default=True)
    context = {
        "token": guid,
        "event": event,
        "next": reverse("registration:findAsstDealer"),
    }
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
    except (ValueError, KeyError):
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
    postData = json.loads(request.body)
    email = postData["email"]
    token = postData["token"]

    try:
        dealer = Dealer.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
    except Dealer.DoesNotExist:
        return HttpResponseNotFound("No Dealer Found " + email)

    request.session["dealer_id"] = dealer.id
    return JsonResponse({"success": True, "message": "DEALER"})


def find_dealer_to_add_assistant_post(request):
    post_data = json.loads(request.body)
    email = post_data.get("email")
    token = post_data.get("token")

    if email is None or token is None:
        return JsonResponse(
            {"success": False, "message": "Email or token missing from form data"},
            status=400,
        )

    try:
        dealer = Dealer.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
    except Dealer.DoesNotExist:
        return HttpResponseNotFound("No dealer found")

    request.session["dealer_id"] = dealer.pk
    return JsonResponse(
        {
            "success": True,
            "message": "DEALER",
            "location": reverse("registration:add_assistants"),
        }
    )


def findAsstDealer(request):
    postData = json.loads(request.body)
    email = postData["email"]
    token = postData["token"]

    try:
        dealer_assistant = DealerAsst.objects.get(
            email__iexact=email, registrationToken=token
        )
    except DealerAsst.DoesNotExist:
        return HttpResponseNotFound("No assistant dealer found")

    # Check if they've already registered:
    if dealer_assistant.attendee is not None:
        # Send them to the upgrade path instead
        request.session["attendee_id"] = dealer_assistant.attendee.pk
        request.session["badge_id"] = dealer_assistant.attendee.badge_set.first().pk
        return JsonResponse(
            {
                "success": True,
                "message": "ASSISTANT",
                "location": reverse("registration:findUpgrade"),
            }
        )

    request.session["assistant_id"] = dealer_assistant.id
    request.session["discount"] = dealer_assistant.event.assistantDiscount.codeName
    return JsonResponse(
        {
            "success": True,
            "message": "ASSISTANT",
            "location": reverse("registration:index"),
        }
    )


def invoiceDealer(request):
    sessionItems = request.session.get("order_items", [])
    sessionDiscount = request.session.get("discount", "")
    if not sessionItems:
        context = {"orderItems": [], "total": 0, "discount": {}}
        clear_session(request)
    else:
        dealerId = request.session.get("dealer_id", -1)
        if dealerId == -1:
            context = {"orderItems": [], "total": 0, "discount": {}}
            clear_session(request)
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


def add_assistants(request):
    context = {"attendee": None, "dealer": None}
    try:
        dealerId = request.session["dealer_id"]
    except (KeyError, ValueError):
        return render(request, "registration/dealer/dealerasst-add.html", context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer.attendee:
        assts = list(DealerAsst.objects.filter(dealer=dealer))
        assistants = []
        for dasst in assts:
            assistants.append(model_to_dict(dasst))
        asst_count_registered = len([ass for ass in assts if ass.attendee is not None])
        context = {
            "attendee": dealer.attendee,
            "dealer": dealer,
            "assistants": assts,
            "extra_assistants_range": range(len(assts), dealer.tableSize.partnerMax),
            "asst_count_registered": asst_count_registered,
            "json_assistants": json.dumps(assistants, default=handler),
        }
    event = Event.objects.get(default=True)
    context["event"] = event
    return render(request, "registration/dealer/dealerasst-add.html", context)


def add_assistants_checkout(request):
    try:
        form_data = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for add_assistants_checkout()")
        return JsonResponse({"success": False})
    billing_data = form_data["billingData"]
    assistants_form = form_data["assistants"]
    dealer_id = request.session["dealer_id"]
    dealer = Dealer.objects.get(id=dealer_id)
    event = Event.objects.get(default=True)

    badge = Badge.objects.filter(attendee=dealer.attendee, event=dealer.event).last()

    priceLevel = badge.effectiveLevel()
    if priceLevel is None:
        return JsonResponse(
            {
                "success": False,
                "message": "Dealer account has not been paid. Please pay for your table before adding assistants.",
            }
        )

    order_item = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")

    for assistant in assistants_form:
        if assistant.get("id"):
            # Update an existing dealer assistant by ID
            dealer_asst = DealerAsst.objects.get(dealer=dealer, id=assistant.get("id"))
        else:
            # Otherwise, create a new one:
            dealer_asst = DealerAsst(
                dealer=dealer,
                event=event,
                name=assistant["name"],
                email=assistant["email"],
                license=assistant["license"],
            )
        try:
            dealer_asst.name = assistant["name"]
            dealer_asst.email = assistant["email"]
            dealer_asst.license = assistant["license"]
            dealer_asst.save()
        except KeyError:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Bad request: name, email, and license fields are required to update assistant",
                }
            )

    unpaid_partner_count = dealer.getUnpaidPartnerCount()

    # FIXME: remove hardcoded costs
    total = Decimal(55 * unpaid_partner_count)
    if billing_data["breakfast"]:
        total = total + Decimal(60 * unpaid_partner_count)

    if total <= 0:
        logger.error(
            f"Error checking out dealer while adding assistants: total too low: {total} <= 0"
        )
        return JsonResponse(
            {
                "success": False,
                "message": "An error occurred while adding your assistants.",
            },
            status=500,
        )

    status, message, order = doCheckout(
        billing_data, total, None, [], [order_item], 0, 0
    )

    if status:
        # Payment succeeded - Mark assistants as paid
        for assistant in dealer.dealerasst_set.all().filter(paid=False):
            assistant.paid = True
            assistant.save()

        clear_session(request)
        try:
            registration.emails.send_dealer_assistant_email(dealer.id)
            # Send registration instruction emails to assistants that haven't registered yet:
            for assistant in dealer.dealerasst_set.all().filter(attendee__isnull=True):
                registration.emails.send_dealer_assistant_registration_invite(assistant)
        except Exception as e:
            logger.error("Error emailing DealerAsstEmail.")
            logger.exception(e)
            dealer_email = getDealerEmail()
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        f"Your payment succeeded but we may have been unable to send you a confirmation email. "
                        f"If you do not receive one within the next hour, please contact {dealer_email} to get your "
                        f"confirmation number."
                    ),
                }
            )
        return JsonResponse({"success": True})
    else:
        # Payment failed
        return JsonResponse({"success": False, "message": message})


def addDealer(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addStaff()")
        logger.exception(e)
        return JsonResponse({"success": False})

    pda = postData["attendee"]
    pdd = postData["dealer"]
    evt = postData["event"]
    pdp = postData["priceLevel"]
    event = Event.objects.get(name=evt)

    if "dealer_id" not in request.session:
        return HttpResponseServerError("Session expired")

    # Update Dealer info
    try:
        dealer = Dealer.objects.get(id=pdd["id"])
    except dealer.DoesNotExist:
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

    dealer.save()

    # Update Attendee info
    try:
        attendee = Attendee.objects.get(id=pda["id"])
    except attendee.DoesNotExist:
        return HttpResponseServerError("Attendee id not found")

    attendee.preferredName = pda.get("preferredName", "")
    attendee.firstName = pda["firstName"]
    attendee.lastName = pda["lastName"]
    attendee.address1 = pda["address1"]
    attendee.address2 = pda["address2"]
    attendee.city = pda["city"]
    attendee.state = pda["state"]
    attendee.country = pda["country"]
    attendee.postalCode = pda["postal"]
    attendee.phone = pda["phone"]

    attendee.save()

    badge = Badge.objects.get(attendee=attendee, event=event)
    badge.badgeName = pda["badgeName"]

    badge.save()

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
    sessionItems = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
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

        clear_session(request)

        try:
            registration.emails.send_dealer_payment_email(dealer, order)
        except Exception as e:
            logger.error("Error sending DealerPaymentEmail - zero sum.")
            logger.exception(e)
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
    pcharity = Decimal(postData.get("charityDonation", "0.00").strip() or "0.00")
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    pbill = postData["billingData"]
    status, message, order = doCheckout(
        pbill, total, discount, None, orderItems, porg, pcharity
    )

    if status:
        for assistant in dealer.dealerasst_set.all():
            assistant.paid = True
            assistant.save()

        clear_session(request)
        try:
            dealer.resetToken()
            registration.emails.send_dealer_payment_email(dealer, order)
        except Exception as e:
            logger.error("Error sending DealerPaymentEmail. " + request.body)
            logger.exception(e)
            dealerEmail = getDealerEmail()
            return JsonResponse(
                {
                    "success": False,
                    "message": "Your registration succeeded but we may have been unable to send you a confirmation "
                    f"email. If you have any questions, please contact {dealerEmail}",
                }
            )
        return JsonResponse({"success": True})
    else:
        order.delete()
        return JsonResponse({"success": False, "message": message})


def addNewDealer(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addNewDealer()")
        return JsonResponse({"success": False})

    # create attendee from request post
    pda = postData["attendee"]
    pdd = postData["dealer"]
    evt = postData["event"]

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))
    event = Event.objects.get(name=evt)

    attendee = Attendee(
        preferredName=pda.get("preferredName", ""),
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
        registration.emails.send_dealer_application_email(dealer.id)
    except Exception as e:
        logger.error("Error sending DealerApplicationEmail.")
        logger.exception(e)
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
    unpaidPartnerCount = dealer.getUnpaidPartnerCount()
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
        + 55 * unpaidPartnerCount
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
