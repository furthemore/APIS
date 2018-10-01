from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import *

def sendRegistrationEmail(order, email):
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
        if oi.badge.attendee.email == email:
            # send payment receipt to the payor
            data = {'reference': order.reference, 'order': order, 'orderItems': orderDict, 'hasMinors': hasMinors}
            msgTxt = render_to_string('registration/emails/registrationPayment.txt', data)
            msgHtml = render_to_string('registration/emails/registrationPayment.html', data)
            sendEmail("registration@furthemore.org", [email], 
                 "Furthemore 2019 Registration Payment", msgTxt, msgHtml)
        else: 
            # send regular emails to everyone else
            data = {'reference': order.reference, 'orderItem': oi}
            msgTxt = render_to_string('registration/emails/registration.txt', data)
            msgHtml = render_to_string('registration/emails/registration.html', data)
            sendEmail("registration@furthemore.org", [oi.badge.attendee.email], 
                 "Furthemore 2019 Registration Confirmation", msgTxt, msgHtml)

        # send vip notification if necessary
        if oi.priceLevel.emailVIP:
            data = {'badge': oi.badge}
            msgTxt = render_to_string('registration/emails/vipNotification.txt', data)
            msgHtml = render_to_string('registration/emails/vipNotification.html', data)
            sendEmail("registration@furthemore.org", [email for email in oi.priceLevel.emailVIPEmails.split(',')], 
                 "Furthemore 2019 VIP Registration", msgTxt, msgHtml)


def sendUpgradePaymentEmail(attendee, order):
    data = {'reference': order.reference}
    orderItems = OrderItem.objects.filter(order=order)
    msgTxt = render_to_string('registration/emails/upgrade.txt', data)
    msgHtml = render_to_string('registration/emails/upgrade.html', data)
    sendEmail("registration@furthemore.org", [attendee.email], "Furthemore 2019 Upgrade Payment", 
              msgTxt, msgHtml)

    for oi in orderItems:
        if oi.priceLevel.emailVIP:
            data = {'badge': oi.badge}
            msgTxt = render_to_string('registration/emails/vipNotification.txt', data)
            msgHtml = render_to_string('registration/emails/vipNotification.html', data)
            sendEmail("registration@furthemore.org", [email for email in oi.priceLevel.emailVIPEmails.split(',')], 
                 "Furthemore 2019 VIP Registration", msgTxt, msgHtml)


def sendStaffRegistrationEmail(orderId):
    order = Order.objects.get(id=orderId)
    email = order.billingEmail
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/staffRegistration.txt', data)
    msgHtml = render_to_string('registration/emails/staffRegistration.html', data)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2019 Staff Registration", 
              msgTxt, msgHtml)

def sendStaffPromotionEmail(staff):
    data = {'registrationToken': staff.registrationToken}
    msgTxt = render_to_string('registration/emails/staffPromotion.txt', data)
    msgHtml = render_to_string('registration/emails/staffPromotion.html', data)
    sendEmail("registration@furthemore.org", [staff.attendee.email], "Welcome to Furthemore Staff!", 
              msgTxt, msgHtml)

def sendNewStaffEmail(token):
    data = {'registrationToken': token.token}
    msgTxt = render_to_string('registration/emails/newStaff.txt', data)
    msgHtml = render_to_string('registration/emails/newStaff.html', data)
    sendEmail("registration@furthemore.org", [token.email], "Welcome to Furthemore Staff!", 
              msgTxt, msgHtml)

def sendDealerApplicationEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}    
    msgTxt = render_to_string('registration/emails/dealer.txt', data)
    msgHtml = render_to_string('registration/emails/dealer.html', data)
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2019 Dealer Application", msgTxt, msgHtml)

    data = {'dealer': dealer}
    msgTxt = render_to_string('registration/emails/dealerNotice.txt', data)
    msgHtml = render_to_string('registration/emails/dealerNotice.html', data)
    sendEmail("marketplace-noreply@furthemore.org", ["marketplacehead@furthemore.org"], 
              "Fur The More 2019 Dealer Application Received", msgTxt, msgHtml)

def sendDealerAsstFormEmail(dealer):
    data = {'dealer': dealer}    
    msgTxt = render_to_string('registration/emails/dealerAsstForm.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsstForm.html', data)
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2019 Dealer Assistant Addition", msgTxt, msgHtml)


def sendDealerAsstEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}    
    msgTxt = render_to_string('registration/emails/dealerAsst.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsst.html', data)
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2019 Dealer Assistant Addition", msgTxt, msgHtml)

    sendEmail("marketplace-noreply@furthemore.org", ["marketplacehead@furthemore.org"], 
              "Fur The More 2019 Dealer Application", "Dealer assistant addition received.", "Dealer asistant addition received.")

def sendDealerPaymentEmail(dealer, order):
    orderItem = OrderItem.objects.filter(order=order).first()
    options = AttendeeOptions.objects.filter(orderItem=orderItem)
    data = {'order': order, 'dealer': dealer, 'orderItem': orderItem, 'options': options}
    msgTxt = render_to_string('registration/emails/dealerPayment.txt', data)
    msgHtml = render_to_string('registration/emails/dealerPayment.html', data)

    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email],
              "Fur The More 2019 Dealer Payment", msgTxt, msgHtml)

def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}
    msgTxt = render_to_string('registration/emails/dealerUpdate.txt', data)
    msgHtml = render_to_string('registration/emails/dealerUpdate.html', data)

    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email],
              "Fur The More 2019 Dealer Information Update", msgTxt, msgHtml)
    

def sendApprovalEmail(dealerQueryset):
    for dealer in dealerQueryset:
        data = {'dealer': dealer}
        msgTxt = render_to_string('registration/emails/dealerApproval.txt', data)
        msgHtml = render_to_string('registration/emails/dealerApproval.html', data)
        sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
                  "Fur The More 2019 Dealer Application", msgTxt, msgHtml)


def sendEmail(replyAddress, toAddressList, subject, message, htmlMessage):
    mailMessage = EmailMultiAlternatives(
      subject,
      message,
      'dragon@furthemore.org',
      toAddressList,
      reply_to=[replyAddress]
    )
    mailMessage.attach_alternative(htmlMessage, "text/html")
    mailMessage.send()
