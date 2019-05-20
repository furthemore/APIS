from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import logging
import sys

from .models import *

if sys.version_info[0] == 2:
    import views
else:
    from . import views

logger = logging.getLogger('registration.emails')

def sendRegistrationEmail(order, email):
    logger.debug("Enter sendRegistrationEmail...")
    orderItems = OrderItem.objects.filter(order=order)
    orderDict = {}
    hasMinors = False
    for oi in orderItems:
        ao = AttendeeOptions.objects.filter(orderItem=oi)
        orderDict[oi] = ao
        if oi.badge.isMinor():
            hasMinors = True


    # send registration confirmations to all people in the order
    for oi in orderItems:
        registrationEmail = views.getRegistrationEmail(oi.badge.event)
        if oi.badge.attendee.email == email:
            # send payment receipt to the payor
            data = {
                'reference': order.reference,
                'order': order,
                'orderItems': orderDict,
                'hasMinors': hasMinors,
                'event' : oi.badge.event
            }
            msgTxt = render_to_string('registration/emails/registrationPayment.txt', data)
            msgHtml = render_to_string('registration/emails/registrationPayment.html', data)
            sendEmail(registrationEmail, [email],
                "{0} Registration Payment".format(oi.badge.event.name), 
                msgTxt, msgHtml)
        else:
            # send regular emails to everyone else
            data = {'reference': order.reference, 'orderItem': oi, 'event': oi.badge.event}
            msgTxt = render_to_string('registration/emails/registration.txt', data)
            msgHtml = render_to_string('registration/emails/registration.html', data)
            sendEmail(registrationEmail, [oi.badge.attendee.email],
                "{0} Registration Confirmation".format(oi.badge.event.name),
                msgTxt, msgHtml)

        # send vip notification if necessary
        if oi.priceLevel.emailVIP:
            data = {'badge': oi.badge, 'event' : oi.badge.event}
            msgTxt = render_to_string('registration/emails/vipNotification.txt', data)
            msgHtml = render_to_string('registration/emails/vipNotification.html', data)
            sendEmail(registrationEmail, [email for email in oi.priceLevel.emailVIPEmails.split(',')],
                 "{0} VIP Registration".format(oi.badge.event.name), msgTxt, msgHtml)

def sendUpgradePaymentEmail(attendee, order):
    orderItems = OrderItem.objects.filter(order=order)
    msgTxt = render_to_string('registration/emails/upgrade.txt', data)
    msgHtml = render_to_string('registration/emails/upgrade.html', data)
    event = Event.objects.get(default=True)
    registrationEmail = views.getRegistraionEmail(event)
    data = {'reference': order.reference, 'event': event}
    sendEmail(registrationEmail, [attendee.email], "{0} Upgrade Payment".format(event.name),
              msgTxt, msgHtml)

    for oi in orderItems:
        if oi.priceLevel.emailVIP:
            data = {'badge': oi.badge, 'event': event}
            msgTxt = render_to_string('registration/emails/vipNotification.txt', data)
            msgHtml = render_to_string('registration/emails/vipNotification.html', data)
            sendEmail(registrationEmail, [email for email in oi.priceLevel.emailVIPEmails.split(',')], 
                 "{0} VIP Registration".format(event.name), msgTxt, msgHtml)


def sendStaffRegistrationEmail(orderId):
    order = Order.objects.get(id=orderId)
    email = order.billingEmail
    event = Event.objects.get(default=True)
    data = {'reference': order.reference, 'event': event}
    msgTxt = render_to_string('registration/emails/staffRegistration.txt', data)
    msgHtml = render_to_string('registration/emails/staffRegistration.html', data)
    event = Event.objects.get(default=True)
    staffEmail = views.getStaffEmail(event)
    sendEmail(staffEmail, [email], "{0} Staff Registration".format(event.name), 
              msgTxt, msgHtml)

def sendStaffPromotionEmail(staff):
    data = {'registrationToken': staff.registrationToken, 'event': staff.event}
    msgTxt = render_to_string('registration/emails/staffPromotion.txt', data)
    msgHtml = render_to_string('registration/emails/staffPromotion.html', data)
    staffEmail = views.getStaffEmail(staff.event)
    sendEmail(staffEmail, [staff.attendee.email], "Welcome to {0} Staff!".format(staff.event.name),
              msgTxt, msgHtml)

def sendNewStaffEmail(token):
    event = Event.objects.get(default=True)
    data = {'registrationToken': token.token, 'event': event}
    msgTxt = render_to_string('registration/emails/newStaff.txt', data)
    msgHtml = render_to_string('registration/emails/newStaff.html', data)
    staffEmail = views.getStaffEmail(event)
    sendEmail(staffEmail, [token.email], "Welcome to {0} Staff!".format(event.name), 
              msgTxt, msgHtml)

def sendDealerApplicationEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {'event' : dealer.event, 'dealer': dealer}
    msgTxt = render_to_string('registration/emails/dealer.txt', data)
    msgHtml = render_to_string('registration/emails/dealer.html', data)
    dealerEmail = views.getDealerEmail(dealer.event)
    sendEmail(dealerEmail, [dealer.attendee.email],
              "{0} Dealer Application".format(dealer.event.name), msgTxt, msgHtml)

    msgTxt = render_to_string('registration/emails/dealerNotice.txt', data)
    msgHtml = render_to_string('registration/emails/dealerNotice.html', data)
    sendEmail(dealerEmail, [dealerEmail,],
              "{0} Dealer Application Received".format(event.name),
              msgTxt, msgHtml)

def sendDealerAsstFormEmail(dealer):
    data = {'dealer': dealer, 'event': dealer.event}
    msgTxt = render_to_string('registration/emails/dealerAsstForm.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsstForm.html', data)
    dealerEmail = views.getDealerEmail(dealer.event)
    sendEmail(dealerEmail, [dealer.attendee.email], 
              "{0} Dealer Assistant Addition".format(dealer.event.name),
              msgTxt, msgHtml)


def sendDealerAsstEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {'dealer': dealer, 'event': dealer.event}
    msgTxt = render_to_string('registration/emails/dealerAsst.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsst.html', data)
    dealerEmail = views.getDealerEmail(dealer.event)
    sendEmail(dealerEmail, [dealer.attendee.email], 
              "{0} Dealer Assistant Addition".format(dealer.event.name),
              msgTxt, msgHtml)


def sendDealerPaymentEmail(dealer, order):
    orderItem = OrderItem.objects.filter(order=order).first()
    options = AttendeeOptions.objects.filter(orderItem=orderItem)
    data = {'order': order, 'dealer': dealer, 'orderItem': orderItem, 'options': options, 'event': dealer.event}
    msgTxt = render_to_string('registration/emails/dealerPayment.txt', data)
    msgHtml = render_to_string('registration/emails/dealerPayment.html', data)
    dealerEmail = views.getDealerEmail(dealer.event)

    sendEmail(dealerEmail, [dealer.attendee.email],
              "{0} Dealer Payment".format(dealer.event.name),
              msgTxt, msgHtml)

def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {'dealer': dealer, 'event': dealer.event}
    msgTxt = render_to_string('registration/emails/dealerUpdate.txt', data)
    msgHtml = render_to_string('registration/emails/dealerUpdate.html', data)
    dealerEmail = views.getDealerEmail(dealer.event)

    sendEmail(dealerEmail, [dealer.attendee.email],
              "{0} Dealer Information Update".format(dealer.event.name),
              msgTxt, msgHtml)


def sendApprovalEmail(dealerQueryset):
    for dealer in dealerQueryset:
        data = {'dealer': dealer, 'event': dealer.event}
        msgTxt = render_to_string('registration/emails/dealerApproval.txt', data)
        msgHtml = render_to_string('registration/emails/dealerApproval.html', data)
        dealerEmail = views.getDealerEmail(dealer.event)
        sendEmail(dealerEmail, [dealer.attendee.email], 
                  "{0} Dealer Application".format(dealer.event.name),
                  msgTxt, msgHtml)


def sendEmail(replyAddress, toAddressList, subject, message, htmlMessage):
    logger.debug("Enter sendEmail...")
    mailMessage = EmailMultiAlternatives(
      subject,
      message,
      settings.APIS_DEFAULT_EMAIL,
      toAddressList,
      reply_to=[replyAddress]
    )
    logger.debug("Message to: {0}".format(toAddressList))
    mailMessage.attach_alternative(htmlMessage, "text/html")
    logger.debug("Sending...")
    mailMessage.send()
    logger.debug("Email sent")
