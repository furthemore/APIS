import logging

from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

import registration.views.common
import registration.views.dealers
import registration.views.staff
from registration.models import *

logger = logging.getLogger("registration.emails")


def _get_event_url(event: Event) -> str:
    if event.websiteUrl:
        return event.websiteUrl

    reg_index = reverse("registration:index")
    site_domain = Site.objects.get_current().domain

    return f"https://{site_domain}{reg_index}"


def send_registration_email(order, email, send_vip=True):
    logger.debug("Enter send_registration_email...")
    order_items = OrderItem.objects.filter(order=order)
    order_dict = {}
    has_minors = False
    for oi in order_items:
        ao = AttendeeOptions.objects.filter(orderItem=oi)
        order_dict[oi] = ao
        if oi.badge.isMinor():
            has_minors = True

    # send registration confirmations to all people in the order
    for oi in order_items:
        registration_email = registration.views.common.get_registration_email(
            oi.badge.event
        )
        if oi.badge.attendee.email == email:
            # send payment receipt to the payor
            data = {
                "reference": order.reference,
                "order": order,
                "orderItems": order_dict,
                "hasMinors": has_minors,
                "event": oi.badge.event,
                "eventUrl": _get_event_url(oi.badge.event),
            }
            msg_txt = render_to_string(
                "registration/emails/registration-payment.txt", data
            )
            msg_html = render_to_string(
                "registration/emails/registration-payment.html", data
            )
            send_email(
                registration_email,
                [email],
                "{0} Registration Payment".format(oi.badge.event.name),
                msg_txt,
                msg_html,
            )
        else:
            # send regular emails to everyone else
            data = {
                "reference": order.reference,
                "orderItem": oi,
                "event": oi.badge.event,
                "eventUrl": _get_event_url(oi.badge.event),
            }
            msg_txt = render_to_string("registration/emails/registration.txt", data)
            msg_html = render_to_string("registration/emails/registration.html", data)
            send_email(
                registration_email,
                [oi.badge.attendee.email],
                "{0} Registration Confirmation".format(oi.badge.event.name),
                msg_txt,
                msg_html,
            )

        # send vip notification if necessary
        if oi.priceLevel.emailVIP and send_vip:
            data = {"badge": oi.badge, "event": oi.badge.event}
            msg_txt = render_to_string("registration/emails/vip-notification.txt", data)
            msg_html = render_to_string(
                "registration/emails/vip-notification.html", data
            )
            send_email(
                registration_email,
                [email for email in oi.priceLevel.emailVIPEmails.split(",")],
                "{0} VIP Registration".format(oi.badge.event.name),
                msg_txt,
                msg_html,
            )


def send_upgrade_instructions(badge):
    event = Event.objects.get(default=True)
    registration_email = registration.views.common.get_registration_email(event)

    data = {
        "event": event,
        "badge": badge,
    }

    msg_txt = render_to_string("registration/emails/upgrade-instructions.txt", data)
    msg_html = render_to_string("registration/emails/upgrade-instructions.html", data)
    send_email(
        registration_email,
        [badge.attendee.email],
        "Upgrade Your Registration for {0}".format(event.name),
        msg_txt,
        msg_html,
    )


def send_upgrade_payment_email(attendee, order):
    event = Event.objects.get(default=True)
    order_items = OrderItem.objects.filter(order=order)
    data = {
        "event": event,
        "reference": order.reference,
    }
    msg_txt = render_to_string("registration/emails/upgrade.txt", data)
    msg_html = render_to_string("registration/emails/upgrade.html", data)
    registration_email = registration.views.common.get_registration_email(event)

    send_email(
        registration_email,
        [attendee.email],
        "{0} Upgrade Payment".format(event.name),
        msg_txt,
        msg_html,
    )

    for oi in order_items:
        if oi.priceLevel.emailVIP:
            data = {"badge": oi.badge, "event": event}
            msg_txt = render_to_string("registration/emails/vip-notification.txt", data)
            msg_html = render_to_string(
                "registration/emails/vip-notification.html", data
            )
            send_email(
                registration_email,
                [email for email in oi.priceLevel.emailVIPEmails.split(",")],
                "{0} VIP Registration".format(event.name),
                msg_txt,
                msg_html,
            )


def send_staff_registration_email(orderId):
    order = Order.objects.get(id=orderId)
    email = order.billingEmail
    event = Event.objects.get(default=True)
    data = {"reference": order.reference, "event": event}
    msg_txt = render_to_string("registration/emails/staff/registration.txt", data)
    msg_html = render_to_string("registration/emails/staff/registration.html", data)
    event = Event.objects.get(default=True)
    staff_email = registration.views.staff.get_staff_email(event)
    send_email(
        staff_email,
        [email],
        "{0} Staff Registration".format(event.name),
        msg_txt,
        msg_html,
    )


def send_staff_promotion_email(staff):
    data = {"registrationToken": staff.registrationToken, "event": staff.event}
    msg_txt = render_to_string("registration/emails/staff/promotion.txt", data)
    msg_html = render_to_string("registration/emails/staff/promotion.html", data)
    staff_email = registration.views.staff.get_staff_email(staff.event)
    send_email(
        staff_email,
        [staff.attendee.email],
        "Welcome to {0} Staff!".format(staff.event.name),
        msg_txt,
        msg_html,
    )


def send_new_staff_email(token):
    event = Event.objects.get(default=True)
    data = {"registrationToken": token.token, "event": event}
    msg_txt = render_to_string("registration/emails/staff/new.txt", data)
    msg_html = render_to_string("registration/emails/staff/new.html", data)
    staff_email = registration.views.staff.get_staff_email(event)
    send_email(
        staff_email,
        [token.email],
        "Welcome to {0} Staff!".format(event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_application_email(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {"event": dealer.event, "dealer": dealer}
    msg_txt = render_to_string("registration/emails/dealer/dealer.txt", data)
    msg_html = render_to_string("registration/emails/dealer/dealer.html", data)
    dealer_email = registration.views.dealers.get_dealer_email(dealer.event)
    send_email(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Application".format(dealer.event.name),
        msg_txt,
        msg_html,
    )

    msg_txt = render_to_string("registration/emails/dealer/dealer-notice.txt", data)
    msg_html = render_to_string("registration/emails/dealer/dealer-notice.html", data)
    send_email(
        dealer_email,
        [
            dealer_email,
        ],
        "{0} Dealer Application Received".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_assistant_form_email(dealer):
    data = {"dealer": dealer, "event": dealer.event}
    msg_txt = render_to_string("registration/emails/dealer/assistant-form.txt", data)
    msg_html = render_to_string("registration/emails/dealer/assistant-form.html", data)
    dealer_email = registration.views.dealers.get_dealer_email(dealer.event)
    send_email(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Assistant Addition".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_assistant_email(dealer_id):
    dealer = Dealer.objects.get(id=dealer_id)
    data = {"dealer": dealer, "event": dealer.event}
    msg_txt = render_to_string("registration/emails/dealer/assistant.txt", data)
    msg_html = render_to_string("registration/emails/dealer/assistant.html", data)
    dealer_email = registration.views.dealers.get_dealer_email(dealer.event)
    send_email(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Assistant Addition".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_assistant_registration_invite(assistant):
    data = {"assistant": assistant, "event": assistant.event}
    msg_txt = render_to_string(
        "registration/emails/dealer/assistant-register.txt", data
    )
    msg_html = render_to_string(
        "registration/emails/dealer/assistant-register.html", data
    )
    dealer_email = registration.views.dealers.get_dealer_email(assistant.event)
    send_email(
        dealer_email,
        [assistant.email],
        "{0} Dealer Assistant Addition".format(assistant.event.name),
        msg_txt,
        msg_html,
    )
    assistant.sent = True
    assistant.save()


def send_dealer_payment_email(dealer, order):
    orderItem = OrderItem.objects.filter(order=order).first()
    options = AttendeeOptions.objects.filter(orderItem=orderItem)
    data = {
        "order": order,
        "dealer": dealer,
        "orderItem": orderItem,
        "options": options,
        "event": dealer.event,
    }
    msg_txt = render_to_string("registration/emails/dealer/payment.txt", data)
    msg_html = render_to_string("registration/emails/dealer/payment.html", data)
    dealer_email = registration.views.dealers.get_dealer_email(dealer.event)

    send_email(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Payment".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_approval_email(dealerQueryset):
    for dealer in dealerQueryset:
        data = {"dealer": dealer, "event": dealer.event}
        msg_txt = render_to_string(
            "registration/emails/dealer/dealer-approval.txt", data
        )
        msg_html = render_to_string(
            "registration/emails/dealer/dealer-approval.html", data
        )
        dealer_email = registration.views.dealers.get_dealer_email(dealer.event)
        send_email(
            dealer_email,
            [dealer.attendee.email],
            "{0} Dealer Application".format(dealer.event.name),
            msg_txt,
            msg_html,
        )


def send_chargeback_notice_email(order):
    event = Event.objects.get(default=True)
    data = {
        "event": event,
        "order": order,
    }
    msg_txt = render_to_string("registration/emails/chargeback-notice.txt", data)
    msg_html = render_to_string("registration/emails/chargeback-notice.html", data)
    registration_email = registration.views.common.get_registration_email(event)
    send_email(
        registration_email,
        [order.billingEmail],
        f"Important information about your {event.name} registration.",
        msg_txt,
        msg_html,
        bcc=[registration_email],
    )


def send_email(reply_address, to_address_list, subject, message, html_message, bcc=[]):
    logger.debug("Enter send_email...")
    mail_message = EmailMultiAlternatives(
        subject,
        message,
        settings.APIS_DEFAULT_EMAIL,
        to_address_list,
        reply_to=[reply_address],
        bcc=bcc,
    )
    logger.debug("Message to: {0}".format(to_address_list))
    mail_message.attach_alternative(html_message, "text/html")
    logger.debug("Sending...")
    mail_message.send()
    logger.debug("Email sent")
