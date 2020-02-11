import json
import time
from datetime import datetime

from attendee import get_attendee_age
from common import logger
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from printing import printNametag

from registration import printing
from registration.models import *
from registration.pushy import PushyAPI


@staff_member_required
def onsiteAdmin(request):
    # Modify a dummy session variable to keep it alive
    request.session["heartbeat"] = time.time()

    event = Event.objects.get(default=True)
    terminals = list(Firebase.objects.all())
    term = request.session.get("terminal", None)
    query = request.GET.get("search", None)

    errors = []
    results = None

    # Set default payment terminal to use:
    if term is None and len(terminals) > 0:
        request.session["terminal"] = terminals[0].id

    if len(terminals) == 0:
        errors.append(
            {
                "type": "danger",
                "code": "ERROR_NO_TERMINAL",
                "text": "It looks like no payment terminals have been configured "
                "for this server yet. Check that the APIS Terminal app is "
                "running, and has been configured for the correct URL and API key.",
            }
        )

    # No terminal selection saved in session - see if one's
    # on the URL (that way it'll survive session timeouts)
    url_terminal = request.GET.get("terminal", None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    if url_terminal is not None:
        try:
            terminal_obj = Firebase.objects.get(id=int(url_terminal))
            request.session["terminal"] = terminal_obj.id
        except Firebase.DoesNotExist:
            errors.append(
                {
                    "type": "warning",
                    "text": "The payment terminal specified has not registered with the server",
                }
            )
        except ValueError:
            # weren't passed an integer
            errors.append({"type": "danger", "text": "Invalid terminal specified"})

    if query is not None:
        results = Badge.objects.filter(
            Q(attendee__lastName__icontains=query)
            | Q(attendee__firstName__icontains=query),
            Q(event=event),
        )
        if len(results) == 0:
            errors.append(
                {"type": "warning", "text": 'No results for query "{0}"'.format(query)}
            )

    context = {
        "terminals": terminals,
        "errors": errors,
        "results": results,
        "printer_uri": settings.REGISTER_PRINTER_URI,
    }

    return render(request, "registration/onsite-admin.html", context)


@staff_member_required
def onsiteAdminSearch(request):
    event = Event.objects.get(default=True)
    terminals = list(Firebase.objects.all())
    query = request.POST.get("search", None)
    if query is None:
        return redirect("onsiteAdmin")

    errors = []
    results = Badge.objects.filter(
        Q(attendee__lastName__icontains=query)
        | Q(attendee__firstName__icontains=query),
        Q(event=event),
    )
    if len(results) == 0:
        errors = [
            {"type": "warning", "text": 'No results for query "{0}"'.format(query)}
        ]

    context = {"terminals": terminals, "errors": errors, "results": results}
    return render(request, "registration/onsite-admin.html", context)


@staff_member_required
def closeTerminal(request):
    data = {"command": "close"}
    return sendMessageToTerminal(request, data)


@staff_member_required
def openTerminal(request):
    data = {"command": "open"}
    return sendMessageToTerminal(request, data)


def sendMessageToTerminal(request, data):
    request.session["heartbeat"] = time.time()  # Keep session alive
    url_terminal = request.GET.get("terminal", None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    session_terminal = request.session.get("terminal", None)

    if url_terminal is not None:
        try:
            active = Firebase.objects.get(id=int(url_terminal))
            request.session["terminal"] = active.id
        except Firebase.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The payment terminal specified has not registered with the server",
                },
                status=500,
            )
        except ValueError:
            # weren't passed an integer
            return JsonResponse(
                {"success": False, "message": "Invalid terminal specified"}, status=400
            )

    try:
        active = Firebase.objects.get(id=session_terminal)
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "No terminal specified and none in session"},
            status=400,
        )

    logger.info("Terminal from session: {0}".format(request.session["terminal"]))

    to = [
        active.token,
    ]

    PushyAPI.sendPushNotification(data, to, None)
    return JsonResponse({"success": True})


@staff_member_required
def enablePayment(request):
    data = {"command": "enable_payment"}
    return sendMessageToTerminal(request, data)


def notifyTerminal(request, data):
    # Generates preview layout based on cart items and sends the result
    # to the apropriate payment terminal for display to the customer
    term = request.session.get("terminal", None)
    if term is None:
        return
    try:
        active = Firebase.objects.get(id=term)
    except Firebase.DoesNotExist:
        return

    html = render_to_string("registration/customer-display.html", data)
    note = render_to_string("registration/customer-note.txt", data)

    logger.info(note)

    if len(data["result"]) == 0:
        display = {"command": "clear"}
    else:
        display = {
            "command": "display",
            "html": html,
            "note": note,
            "total": int(data["total"] * 100),
            "reference": data["reference"],
        }

    logger.info(display)

    # Send cloud push message
    logger.debug(note)
    to = [
        active.token,
    ]

    PushyAPI.sendPushNotification(display, to, None)


@staff_member_required
def onsiteSelectTerminal(request):
    selected = request.POST.get("terminal", None)
    try:
        active = Firebase.objects.get(id=selected)
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "reason": "Terminal does not exist"}, status=404
        )
    request.session["terminal"] = selected
    return JsonResponse({"success": True})


def assignBadgeNumber(request):
    badge_id = request.POST.get("id")
    badge_number = request.POST.get("number")
    badge_name = request.POST.get("badge", None)
    badge = None
    event = Event.objects.get(default=True)
    logger.info(
        "assignBadgeNumber: id='{0}' badge_nembr='{1}' badge_name='{2}'".format(
            badge_id, badge_number, badge_name
        )
    )

    if badge_name is not None:
        try:
            badge = Badge.objects.filter(
                badgeName__icontains=badge_name, event__name=event.name
            ).first()
        except BaseException:
            return JsonResponse(
                {"success": False, "reason": "Badge name search returned no results"}
            )
    else:
        if badge_id is None or badge_number is None:
            return JsonResponse(
                {"success": False, "reason": "id and number are required parameters"},
                status=400,
            )

    try:
        badge_number = int(badge_number)
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Badge number must be an integer"}, status=400
        )
    logger.info("assignBadgeNumber: int(badge_number) = {0}".format(badge_number))

    if badge is None:
        try:
            badge = Badge.objects.get(id=int(badge_id))
        except Badge.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Badge ID specified does not exist"},
                status=404,
            )
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "Badge ID must be an integer"}, status=400
            )

    try:
        if badge_number < 0:
            # Auto assign
            badges = Badge.objects.filter(event=badge.event)
            highest = badges.aggregate(Max("badgeNumber"))["badgeNumber__max"]
            highest = highest + 1
            badge.badgeNumber = highest
        else:
            badge.badgeNumber = badge_number
        badge.save(update_fields=["badgeNumber"])
        logger.info(
            "assignBadgeNumber: Badge number saved - {0}".format(badge.badgeNumber)
        )
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": "Error while saving badge number",
                "error": str(e),
            },
            status=500,
        )

    return JsonResponse({"success": True})


@staff_member_required
def onsitePrintBadges(request):
    badge_list = request.GET.getlist("id")
    con = printing.Main(local=True)
    tags = []
    theme = ""

    for badge_id in badge_list:
        try:
            badge = Badge.objects.get(id=badge_id)
        except Badge.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Badge id {0} does not exist".format(badge_id),
                },
                status=404,
            )

        theme = badge.event.badgeTheme

        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "{:04}".format(badge.badgeNumber)

        tags.append(
            {
                "name": badge.badgeName,
                "number": badgeNumber,
                "level": str(badge.effectiveLevel()),
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()

    if theme == "":
        theme == "apis"
    con.nametags(tags, theme=theme)
    pdf_path = con.pdf.split("/")[-1]

    file_url = reverse(printNametag) + "?file={0}".format(pdf_path)

    return JsonResponse(
        {
            "success": True,
            "file": pdf_path,
            "next": request.get_full_path(),
            "url": file_url,
        }
    )


def onsiteSignature(request):
    context = {}
    return render(request, "registration/signature.html", context)


@csrf_exempt
def completeSquareTransaction(request):
    key = request.GET.get("key", "")
    reference = request.GET.get("reference", None)
    clientTransactionId = request.GET.get("clientTransactionId", None)
    serverTransactionId = request.GET.get("serverTransactionId", None)

    if key != settings.REGISTER_KEY:
        return JsonResponse(
            {"success": False, "reason": "Incorrect API key"}, status=401
        )

    if reference is None or clientTransactionId is None:
        return JsonResponse(
            {
                "success": False,
                "reason": "Reference and clientTransactionId are required parameters",
            },
            status=400,
        )

    # Things we need:
    #   orderID or reference (passed to square by metadata)
    # Square returns:
    #   clientTransactionId (offline payments)
    #   serverTransactionId (online payments)

    try:
        # order = Order.objects.get(reference=reference)
        orders = Order.objects.filter(reference=reference)
    except Order.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "reason": "No order matching the reference specified exists",
            },
            status=404,
        )

    for order in orders:
        order.billingType = Order.CREDIT
        order.status = Order.COMPLETED
        order.settledDate = datetime.now()
        order.notes = json.dumps(
            {
                "type": "square_register",
                "clientTransactionId": clientTransactionId,
                "serverTransactionId": serverTransactionId,
            }
        )
        # FIXME: Call out to the Square API to populate the transaction details server-side:

        order.save()

    return JsonResponse({"success": True})


def completeCashTransaction(request):
    reference = request.GET.get("reference", None)
    total = request.GET.get("total", None)
    tendered = request.GET.get("tendered", None)

    if reference is None or tendered is None or total is None:
        return JsonResponse(
            {
                "success": False,
                "reason": "Reference, tendered, and total are required parameters",
            },
            status=400,
        )

    try:
        order = Order.objects.get(reference=reference)
    except Order.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "reason": "No order matching the reference specified exists",
            },
            status=404,
        )

    order.billingType = Order.CASH
    order.status = Order.COMPLETED
    order.settledDate = datetime.now()
    order.notes = json.dumps({"type": "cash", "tendered": tendered})
    order.save()

    txn = Cashdrawer(
        action=Cashdrawer.TRANSACTION, total=total, tendered=tendered, user=request.user
    )
    txn.save()

    return JsonResponse({"success": True})


@csrf_exempt
def firebaseRegister(request):
    key = request.GET.get("key", "")
    if key != settings.REGISTER_KEY:
        return JsonResponse(
            {"success": False, "reason": "Incorrect API key"}, status=401
        )

    token = request.GET.get("token", None)
    name = request.GET.get("name", None)
    if token is None or name is None:
        return JsonResponse(
            {"success": False, "reason": "Must specify token and name parameter"},
            status=400,
        )

    # Upsert if a new token with an existing name tries to register
    try:
        old_terminal = Firebase.objects.get(name=name)
        old_terminal.token = token
        old_terminal.save()
        return JsonResponse({"success": True, "updated": True})
    except Firebase.DoesNotExist:
        pass
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "reason": "Failed while attempting to update existing name entry",
            },
            status=500,
        )

    try:
        terminal = Firebase(token=token, name=name)
        terminal.save()
    except Exception as e:
        logger.exception(e)
        logger.error("Error while saving Firebase token to database")
        return JsonResponse(
            {"success": False, "reason": "Error while saving to database"}, status=500
        )

    return JsonResponse({"success": True, "updated": False})


@csrf_exempt
def firebaseLookup(request):
    # Returns the common name stored for a given firebase token
    # (So client can notify server if either changes)
    token = request.GET.get("token", None)
    if token is None:
        return JsonResponse(
            {"success": False, "reason": "Must specify token parameter"}, status=400
        )

    try:
        terminal = Firebase.objects.get(token=token)
        return JsonResponse(
            {"success": True, "name": terminal.name, "closed": terminal.closed}
        )
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "reason": "No such token registered"}, status=404
        )


@staff_member_required
def onsiteAdminCart(request):
    # Returns dataset to render onsite cart preview
    request.session["heartbeat"] = time.time()  # Keep session alive
    cart = request.session.get("cart", None)
    if cart is None:
        return JsonResponse({"success": False, "reason": "Cart not initialized"})

    badges = []
    for id in cart:
        try:
            badge = Badge.objects.get(id=id)
            badges.append(badge)
        except Badge.DoesNotExist:
            cart.remove(id)
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(id)
            )

    order = None
    subtotal = 0
    result = []
    first_order = None
    for badge in badges:
        oi = badge.getOrderItems()
        level = None
        for item in oi:
            level = item.priceLevel
            # WHY?
            if item.order is not None:
                order = item.order
        if level is None:
            effectiveLevel = None
        else:
            effectiveLevel = {"name": level.name, "price": level.basePrice}
            subtotal += level.basePrice

        order = badge.getOrder()
        if first_order is None:
            first_order = order
        else:
            # Reassign order references of items in cart to match first:
            order = badge.getOrder()
            order.reference = first_order.reference
            order.save()

        item = {
            "id": badge.id,
            "firstName": badge.attendee.firstName,
            "lastName": badge.attendee.lastName,
            "badgeName": badge.badgeName,
            "abandoned": badge.abandoned,
            "effectiveLevel": effectiveLevel,
            "discount": badge.getDiscount(),
            "age": get_attendee_age(badge),
        }
        result.append(item)

    total = subtotal
    charityDonation = "?"
    orgDonation = "?"
    if order is not None:
        total += order.orgDonation + order.charityDonation
        charityDonation = order.charityDonation
        orgDonation = order.orgDonation

    data = {
        "success": True,
        "result": result,
        "total": total,
        "charityDonation": charityDonation,
        "orgDonation": orgDonation,
    }

    if order is not None:
        data["order_id"] = order.id
        data["reference"] = order.reference
    else:
        data["order_id"] = None
        data["reference"] = None

    notifyTerminal(request, data)

    return JsonResponse(data)


@staff_member_required
def onsiteAddToCart(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
        )

    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = [
            id,
        ]
        return JsonResponse({"success": True, "cart": [id]})

    if id in cart:
        return JsonResponse({"success": True, "cart": cart})

    cart.append(id)
    request.session["cart"] = cart

    return JsonResponse({"success": True, "cart": cart})


@staff_member_required
def onsiteRemoveFromCart(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
        )

    cart = request.session.get("cart", None)
    if cart is None:
        return JsonResponse({"success": False, "reason": "Cart is empty"})

    try:
        cart.remove(id)
        request.session["cart"] = cart
    except ValueError:
        return JsonResponse({"success": False, "cart": cart, "reason": "Not in cart"})

    return JsonResponse({"success": True, "cart": cart})


@staff_member_required
def onsiteAdminClearCart(request):
    request.session["cart"] = []
    sendMessageToTerminal(request, {"command": "clear"})
    return onsiteAdmin(request)
