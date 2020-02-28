import logging

import views
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import registration.views.common
import registration.views.dealers
import registration.views.staff

from .models import *

logger = logging.getLogger("registration.emails")


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
        registration_email = registration.views.common.getRegistrationEmail(
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
            }
            msg_txt = render_to_string(
                "registration/emails/registrationPayment.txt", data
            )
            msg_html = render_to_string(
                "registration/emails/registrationPayment.html", data
            )
            sendEmail(
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
            }
            msg_txt = render_to_string("registration/emails/registration.txt", data)
            msg_html = render_to_string("registration/emails/registration.html", data)
            sendEmail(
                registration_email,
                [oi.badge.attendee.email],
                "{0} Registration Confirmation".format(oi.badge.event.name),
                msg_txt,
                msg_html,
            )

        # send vip notification if necessary
        if oi.priceLevel.emailVIP and send_vip:
            data = {"badge": oi.badge, "event": oi.badge.event}
            msg_txt = render_to_string("registration/emails/vipNotification.txt", data)
            msg_html = render_to_string(
                "registration/emails/vipNotification.html", data
            )
            sendEmail(
                registration_email,
                [email for email in oi.priceLevel.emailVIPEmails.split(",")],
                "{0} VIP Registration".format(oi.badge.event.name),
                msg_txt,
                msg_html,
            )


def send_upgrade_instructions(badge):
    event = Event.objects.get(default=True)
    registration_email = registration.views.common.getRegistrationEmail(event)

    data = {
        "event": event,
        "badge": badge,
    }

    msg_txt = render_to_string("registration/emails/upgrade-instructions.txt", data)
    msg_html = render_to_string("registration/emails/upgrade-instructions.html", data)
    sendEmail(
        registration_email,
        [badge.attendee.email],
        "Upgrade Your Registration for {0}".format(event.name),
        msg_txt,
        msg_html,
    )


def sendUpgradePaymentEmail(attendee, order):
    event = Event.objects.get(default=True)
    order_items = OrderItem.objects.filter(order=order)
    data = {
        "event": event,
        "reference": order.reference,
    }
    msg_txt = render_to_string("registration/emails/upgrade.txt", data)
    msg_html = render_to_string("registration/emails/upgrade.html", data)
    registration_email = registration.views.common.getRegistrationEmail(event)

    sendEmail(
        registration_email,
        [attendee.email],
        "{0} Upgrade Payment".format(event.name),
        msg_txt,
        msg_html,
    )

    for oi in order_items:
        if oi.priceLevel.emailVIP:
            data = {"badge": oi.badge, "event": event}
            msg_txt = render_to_string("registration/emails/vipNotification.txt", data)
            msg_html = render_to_string(
                "registration/emails/vipNotification.html", data
            )
            sendEmail(
                registration_email,
                [email for email in oi.priceLevel.emailVIPEmails.split(",")],
                "{0} VIP Registration".format(event.name),
                msg_txt,
                msg_html,
            )


def sendStaffRegistrationEmail(orderId):
    order = Order.objects.get(id=orderId)
    email = order.billingEmail
    event = Event.objects.get(default=True)
    data = {"reference": order.reference, "event": event}
    msg_txt = render_to_string("registration/emails/staffRegistration.txt", data)
    msg_html = render_to_string("registration/emails/staffRegistration.html", data)
    event = Event.objects.get(default=True)
    staff_email = registration.views.staff.getStaffEmail(event)
    sendEmail(
        staff_email,
        [email],
        "{0} Staff Registration".format(event.name),
        msg_txt,
        msg_html,
    )


def send_staff_promotion_email(staff):
    data = {"registrationToken": staff.registrationToken, "event": staff.event}
    msg_txt = render_to_string("registration/emails/staffPromotion.txt", data)
    msg_html = render_to_string("registration/emails/staffPromotion.html", data)
    staff_email = registration.views.staff.getStaffEmail(staff.event)
    sendEmail(
        staff_email,
        [staff.attendee.email],
        "Welcome to {0} Staff!".format(staff.event.name),
        msg_txt,
        msg_html,
    )


def send_new_staff_email(token):
    event = Event.objects.get(default=True)
    data = {"registrationToken": token.token, "event": event}
    msg_txt = render_to_string("registration/emails/newStaff.txt", data)
    msg_html = render_to_string("registration/emails/newStaff.html", data)
    staff_email = registration.views.staff.getStaffEmail(event)
    sendEmail(
        staff_email,
        [token.email],
        "Welcome to {0} Staff!".format(event.name),
        msg_txt,
        msg_html,
    )


def sendDealerApplicationEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {"event": dealer.event, "dealer": dealer}
    msg_txt = render_to_string("registration/emails/dealer.txt", data)
    msg_html = render_to_string("registration/emails/dealer.html", data)
    dealer_email = registration.views.dealers.getDealerEmail(dealer.event)
    sendEmail(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Application".format(dealer.event.name),
        msg_txt,
        msg_html,
    )

    msg_txt = render_to_string("registration/emails/dealerNotice.txt", data)
    msg_html = render_to_string("registration/emails/dealerNotice.html", data)
    sendEmail(
        dealer_email,
        [dealer_email,],
        "{0} Dealer Application Received".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_dealer_asst_form_email(dealer):
    data = {"dealer": dealer, "event": dealer.event}
    msg_txt = render_to_string("registration/emails/dealerAsstForm.txt", data)
    msg_html = render_to_string("registration/emails/dealerAsstForm.html", data)
    dealer_email = registration.views.dealers.getDealerEmail(dealer.event)
    sendEmail(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Assistant Addition".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def sendDealerAsstEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {"dealer": dealer, "event": dealer.event}
    msg_txt = render_to_string("registration/emails/dealerAsst.txt", data)
    msg_html = render_to_string("registration/emails/dealerAsst.html", data)
    dealer_email = registration.views.dealers.getDealerEmail(dealer.event)
    sendEmail(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Assistant Addition".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


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
    msg_txt = render_to_string("registration/emails/dealerPayment.txt", data)
    msg_html = render_to_string("registration/emails/dealerPayment.html", data)
    dealer_email = registration.views.dealers.getDealerEmail(dealer.event)

    sendEmail(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Payment".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {"dealer": dealer, "event": dealer.event}
    msg_txt = render_to_string("registration/emails/dealerUpdate.txt", data)
    msg_html = render_to_string("registration/emails/dealerUpdate.html", data)
    dealer_email = registration.views.dealers.getDealerEmail(dealer.event)

    sendEmail(
        dealer_email,
        [dealer.attendee.email],
        "{0} Dealer Information Update".format(dealer.event.name),
        msg_txt,
        msg_html,
    )


def send_approval_email(dealerQueryset):
    for dealer in dealerQueryset:
        data = {"dealer": dealer, "event": dealer.event}
        msg_txt = render_to_string("registration/emails/dealerApproval.txt", data)
        msg_html = render_to_string("registration/emails/dealerApproval.html", data)
        dealer_email = registration.views.dealers.getDealerEmail(dealer.event)
        sendEmail(
            dealer_email,
            [dealer.attendee.email],
            "{0} Dealer Application".format(dealer.event.name),
            msg_txt,
            msg_html,
        )


def sendEmail(reply_address, to_address_list, subject, message, html_message):
    logger.debug("Enter sendEmail...")
    mail_message = EmailMultiAlternatives(
        subject,
        message,
        settings.APIS_DEFAULT_EMAIL,
        to_address_list,
        reply_to=[reply_address],
    )
    logger.debug("Message to: {0}".format(to_address_list))
    mail_message.attach_alternative(html_message, "text/html")
    logger.debug("Sending...")
    mail_message.send()
    logger.debug("Email sent")
